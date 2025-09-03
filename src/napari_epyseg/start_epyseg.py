from napari.utils.history import get_save_history, update_save_history 
from napari import current_viewer
import os
from magicgui import magicgui
from napari.layers import Image
import numpy as np
from napari.utils import notifications as nt
from napari.utils import progress # type: ignore

from epyseg.deeplearning.deepl import EZDeepLearning

from PIL import Image as pilImage
import os
import tempfile
import tifffile as tif
import pathlib

def start_epyseg():
    global cdir
    hist = get_save_history()
    cdir = hist[0]
    viewer = current_viewer()
    paras = dict()
    paras["overlap_width"] = 32
    paras["overlap_height"] = 32
    paras["tile_width"] = 256
    paras["tile_height"] = 256
    paras["norm_min"] = 0
    paras["norm_max"] = 1
    return choose_parameters( viewer, paras )

def choose_parameters( viewer, parameters ):
    @magicgui(call_button="Save segmentation",
            save_file={"label": "Segmentation filename", "mode": "w"},
            )
    def save_interface(
        save_file = pathlib.Path(os.path.join(cdir)),
        ):
        """ Save file interface """
        if not str(save_file).endswith(".tif"):
            nt.show_warning("Unvalid segmentation filename (should be a tif file), set it to a correct file path")
            return
        update_save_history(save_file)
        save_segmentation_file( str(save_file), viewer )

    def show_model_file():
        """ Show/hide the model file interface (if custom is selected) """
        get_parameters.model_file.visible = (get_parameters.model.value == "custom model")
    
    def show_parameters():
        """ Handle advanced parameters visibility """
        get_parameters.overlap_width.visible = (get_parameters.advanced.value == True)
        get_parameters.overlap_height.visible = (get_parameters.advanced.value == True)
        get_parameters.tile_width.visible = (get_parameters.advanced.value == True)
        get_parameters.tile_height.visible = (get_parameters.advanced.value == True)
        get_parameters.normalization_min_percentile.visible = (get_parameters.advanced.value == True)
        get_parameters.normalization_max_percentile.visible = (get_parameters.advanced.value == True)

    def show_channel():
        """ Show/hide channel choice depending on selected layer """
        shape = get_parameters.image.value.data.shape
        print(shape)
        get_parameters.channel.visible = (len(shape)>3)

    def display_channel():
        """ Display the selected channel """
        img = viewer.layers[ get_parameters.image.value.name ].data
        chan_axis = 1
        ## check that the color channel axis is the second one
        if img.shape[0] < img.shape[1]:
            chan_axis = 0
        chan_nb = get_parameters.channel.value
        if (chan_nb < 0) or (chan_nb>img.shape[chan_axis]):
            nt.show_warning("Invalid channel number, set a value in the correct range: [0-"+str(img.shape[chan_axis]-1)+"]")
            return 
        viewer.dims.set_point( chan_axis, get_parameters.channel.value )
        


    @magicgui(call_button="Segment",
            image={'label': 'Pick an Image'},
            model={'label': 'Model to use', "choices": ['epyseg default(v2)', 'custom model']},
            model_file = {'label': 'Custom model file (.h5)'},
            normalization_min_percentile={"widget_type": "LiteralEvalLineEdit"},
            normalization_max_percentile={"widget_type": "LiteralEvalLineEdit"},
            tile_width={"widget_type": "LiteralEvalLineEdit"},
            tile_height={"widget_type": "LiteralEvalLineEdit"},
            overlap_width={"widget_type": "LiteralEvalLineEdit"},
            overlap_height={"widget_type": "LiteralEvalLineEdit"},
            )
    def get_parameters( 
            image: Image,
            channel: int=0,
            model = "epyseg default(v2)",
            model_file = pathlib.Path(cdir),
            advanced = False,
            normalization_min_percentile = parameters["norm_min"],
            normalization_max_percentile = parameters["norm_max"],
            tile_width = parameters["tile_width"],
            tile_height = parameters["tile_height"],
            overlap_width = parameters["overlap_width"],
            overlap_height = parameters["overlap_height"],
            ):
        """ Choose the parameters to run Epyseg on selected file """
        parameters["tile_width"] = tile_width
        parameters["tile_height"] = tile_height
        parameters["overlap_width"] = overlap_width
        parameters["overlap_height"] = overlap_height
        parameters["norm_min"] = normalization_min_percentile
        parameters["norm_max"] = normalization_max_percentile
        parameters["model"] = model
        parameters["model_file"] = str(model_file)
        img = image.data
        chan_axis = 1
        if len(img.shape) > 3:
            if img.shape[0] < img.shape[1]:
                img = img[channel,]
                chan_axis = 0
            else:
                img = img[:,channel,]
        viewer.window._status_bar._toggle_activity_dock( True )
        res = run_epyseg( img, parameters )
        viewer.window._status_bar._toggle_activity_dock( False )
        if len(res.shape) < len(image.data.shape):
            res = np.expand_dims( res, axis=chan_axis )
        viewer.add_image( res, scale=image.scale, blending="additive", name="Segmentation" )
        viewer.window.add_dock_widget( save_interface )
    
    get_parameters.model.changed.connect( show_model_file )
    get_parameters.image.changed.connect( show_channel )
    get_parameters.channel.changed.connect( display_channel )
    get_parameters.model_file.visible = False
    get_parameters.advanced.changed.connect( show_parameters )
    wid = viewer.window.add_dock_widget( get_parameters )
    show_parameters()
    return wid



def run_epyseg_onfolder( input_folder, paras ):
    """ Run EpySeg on all the images in the temporary folder """
    try:
        deepTA = EZDeepLearning()
    except:
        print('EPySeg failed to load.')

    # Load a pre-trained model
    pretrained_model_name = 'Linknet-vgg16-sigmoid-v2'
    pretrained_model_parameters = deepTA.pretrained_models[pretrained_model_name]

    deepTA.load_or_build(model=None, model_weights=None,
                             architecture=pretrained_model_parameters['architecture'], backbone=pretrained_model_parameters['backbone'],
                             activation=pretrained_model_parameters['activation'], classes=pretrained_model_parameters['classes'],
                             input_width=pretrained_model_parameters['input_width'], input_height=pretrained_model_parameters['input_height'],
                             input_channels=pretrained_model_parameters['input_channels'],pretraining=pretrained_model_name)
    #epydir = os.path.join(os.path.abspath(".."), "epyseg_net")
    if paras["model"] == "custom model":
        nt.show_info( "Loading model "+paras["model_file"] )
        if not os.path.exists( paras["model_file"] ):
            nt.show_warning( "Model "+paras["model_file"]+" not found" )
            return None
        deepTA.load_weights( paras["model_file"] )

    input_val_width = int( paras["tile_width"] )
    input_val_height = int( paras["tile_height"] )

    input_shape = deepTA.get_inputs_shape()
    output_shape = deepTA.get_outputs_shape()
    if input_shape[0][-2] is not None:
        input_val_width=input_shape[0][-2]
    if input_shape[0][-3] is not None:
        input_val_height=input_shape[0][-3]
    print(input_shape)
    deepTA.compile(optimizer='adam', loss='bce_jaccard_loss', metrics=['iou_score'])

    minp = float( paras["norm_min"])
    maxp = float( paras["norm_max"])
    range_input = [minp, maxp]
    input_normalization = {'method': 'Rescaling (min-max normalization)',
                        'individual_channels': True, 'range': range_input, 'clip': True}

    predict_generator = deepTA.get_predict_generator(
            inputs=[input_folder], input_shape=input_shape,
            output_shape=output_shape,
            default_input_tile_width=input_val_width,
            default_input_tile_height=input_val_height,
            tile_width_overlap=int(paras["overlap_width"]),
            tile_height_overlap=int(paras["overlap_height"]),
            input_normalization=input_normalization,
            clip_by_frequency={'lower_cutoff': None, 'upper_cutoff': None, 'channel_mode': True} )

    post_process_parameters={}
    post_process_parameters['filter'] = None
    post_process_parameters['correction_factor'] = 1
    post_process_parameters['restore_safe_cells'] = False ## no eff
    post_process_parameters['cutoff_cell_fusion'] = None
    post_proc_method = 'Rescaling (min-max normalization)'
    post_process_parameters['post_process_algorithm'] = post_proc_method
    post_process_parameters['threshold'] = None  # None means autothrehsold # maybe add more options some day

    predict_output_folder = os.path.join(input_folder, 'predict')
    print("Starting segmentation with EpySeg.....")
    deepTA.predict(predict_generator,
                output_shape,
                predict_output_folder=predict_output_folder,
                batch_size=1, **post_process_parameters)

    deepTA.clear_mem()
    if not os.access(predict_output_folder, os.W_OK):
        os.chmod(predict_output_folder, stat.S_IWUSR)
    #deepTA = None
    del deepTA

def run_epyseg( img, paras, verbose=True):
    """ Run EpySeg on selected image or movie - Use a temporary directory """

    tmpdir_path = None
    filename = "image"
    movie = []

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            print("tmp dir "+str(tmpdir))

            ### empty dirnectory if exists
            inputname = filename+"_"
            # if 2D image makes it 3D so that everything is handled the same
            if len(img.shape) == 2:
                img = np.expand_dims( img, axis=0 )
            progress_bar = progress( len(img) )
            progress_bar.set_description( "Running epyseg on all frames..." )
            progress_bar.update(0)
            for i, imslice in enumerate(img):
                with pilImage.fromarray(imslice) as im:
                    numz = "{0:0=5d}".format(i)
                    im.save(os.path.join(tmpdir,inputname+"z"+numz+".tif"))
            try:
                predict_output_folder = os.path.join(tmpdir, 'predict')
                os.makedirs(predict_output_folder, exist_ok=True)
            except:
                print("Warning, issue in creating "+predict_output_folder+" folder")

            progress_bar.update(1)
            ## run Epyseg on tmp directory (contains current image)
            run_epyseg_onfolder( tmpdir, paras )
            progress_bar.update(2)

            ## return result and delete files
            for i in range(len(img)):
                numz = "{0:0=5d}".format(i)
                im = pilImage.open(os.path.join(tmpdir,"predict",inputname+"z"+numz+".tif"))
                movie.append( np.copy(im) )
                im.close()
            os.chmod(os.path.join(tmpdir, "predict", inputname), 0o777)
            os.remove( os.path.join(tmpdir, "predict", inputname) )
            progress_bar.close()
    except:
        pass

    return np.array( movie )

def save_segmentation_file( filename, viewer ):
    """ Save the segmentation results to file """
    if "Segmentation" not in viewer.layers:
        nt.show_warning("No segmentation found")
        return
    lay = viewer.layers["Segmentation"]
    laydata = lay.data
    if len(laydata.shape) > 3:
        laydata = lay.data[:,0,:,:]

    writeTif( laydata, filename, lay.scale, "uint8", what="Segmentation" )

def writeTif(img, imgname, scale, imtype, what=""):
    """ Write image in tif format """
    if len(img.shape) == 2:
        tif.imwrite(imgname, np.array(img, dtype=imtype), imagej=True, resolution=[1./scale[2], 1./scale[1]], metadata={'unit': 'um', 'axes': 'YX'})
    else:
        try:
            tif.imwrite(imgname, np.array(img, dtype=imtype), imagej=True, resolution=[1./scale[2], 1./scale[1]], metadata={'unit': 'um', 'axes': 'TYX'})
        except:
            tif.imwrite(imgname, np.array(img, dtype=imtype), imagej=True, resolution=[1./scale[2], 1./scale[1]], metadata={'unit': 'um', 'axes': 'TYX'})
    nt.show_info(what+" saved in "+imgname)
