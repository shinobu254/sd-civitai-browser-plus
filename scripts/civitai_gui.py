import gradio as gr
from modules import script_callbacks, shared
import os
import json
import fnmatch
import re
from modules.shared import opts, cmd_opts
from modules.paths import extensions_dir
import scripts.civitai_global as gl
import scripts.civitai_download as _download
import scripts.civitai_file_manage as _file
import scripts.civitai_api as _api
from time import sleep

gl.init()

def insert_sub(model_name, version_name):
    insert_sub = getattr(opts, "insert_sub", True)
    try:
        sub_folders = ["None"]
        try:
            version = version_name.replace(" [Installed]", "")
        except:
            version = version_name
        
        if model_name is not None:
            selected_content_type = None
            for item in gl.json_data['items']:
                if item['name'] == model_name:
                    selected_content_type = item['type']
                    desc = item['description']
             
            model_folder = os.path.join(_api.contenttype_folder(selected_content_type, desc))
            for root, dirs, _ in os.walk(model_folder):
                for d in dirs:
                    sub_folder = os.path.relpath(os.path.join(root, d), model_folder)
                    if sub_folder:
                        sub_folders.append(f'{os.sep}{sub_folder}')
        
        sub_folders.remove("None")
        sub_folders = sorted(sub_folders)
        sub_folders.insert(0, "None")
        if insert_sub:
            sub_folders.insert(1, os.path.join(os.sep, model_name))
            sub_folders.insert(2, os.path.join(os.sep, model_name, version))
        
        list = set()
        sub_folders = [x for x in sub_folders if not (x in list or list.add(x))]
        
        return gr.Dropdown.update(choices=sub_folders)
    except:
        return gr.Dropdown.update(choices=None)

def saveSettings(ust, ct, pt, st, bf, cj, td, sn, ss, ts):
    config = cmd_opts.ui_config_file

    # Create a dictionary to map the settings to their respective variables
    settings_map = {
        "civitai_interface/Search type:/value": ust,
        "civitai_interface/Content type:/value": ct,
        "civitai_interface/Time period:/value": pt,
        "civitai_interface/Sort by:/value": st,
        "civitai_interface/Base model:/value": bf,
        "civitai_interface/Save tags after download/value": cj,
        "civitai_interface/Divide cards by date/value": td,
        "civitai_interface/NSFW content/value": sn,
        "civitai_interface/Tile size:/value": ss,
        "civitai_interface/Tile count:/value": ts
    }
    
    # Load the current contents of the config file into a dictionary
    with open(config, 'r') as file:
        data = json.load(file)

    # Remove any keys containing the text `civitai_interface`
    keys_to_remove = [key for key in data if "civitai_interface" in key]
    for key in keys_to_remove:
        del data[key]

    # Update the dictionary with the new settings
    data.update(settings_map)

    # Save the modified content back to the file
    with open(config, 'w') as file:
        json.dump(data, file, indent=4)
        print(f"Updated settings to: {config}")
        
def on_ui_tabs():    
    use_LORA = getattr(opts, "use_LORA", False)
    lobe_directory = None
    
    for root, dirs, files in os.walk(extensions_dir):
        for dir_name in fnmatch.filter(dirs, '*lobe*'):
            lobe_directory = os.path.join(root, dir_name)
            break

    component_id = "togglesL" if lobe_directory else "toggles"
    toggle1 = "toggle1L" if lobe_directory else "toggle1"
    toggle2 = "toggle2L" if lobe_directory else "toggle2"
    toggle3 = "toggle3L" if lobe_directory else "toggle3"
    refreshbtn = "refreshBtnL" if lobe_directory else "refreshBtn"
    filterBox = "filterBoxL" if lobe_directory else "filterBox"
    
    if use_LORA:
        content_choices = ["Checkpoint", "TextualInversion", "LORA & LoCon", "Poses", "Controlnet", "Hypernetwork", "AestheticGradient", "VAE", "Upscaler", "MotionModule", "Wildcards", "Workflows", "Other"] 
    else:
        content_choices = ["Checkpoint", "TextualInversion", "LORA", "LoCon", "Poses", "Controlnet", "Hypernetwork", "AestheticGradient", "VAE", "Upscaler", "MotionModule", "Wildcards", "Workflows", "Other"]
    
    with gr.Blocks() as civitai_interface:
        with gr.Tab(label="Browser", elem_id="browserTab"):
            with gr.Row(elem_id="searchRow"):
                with gr.Accordion(label="", open=False, elem_id=filterBox):
                    with gr.Row():
                        use_search_term = gr.Radio(label="Search type:", choices=["Model name", "User name", "Tag"],value="Model name", elem_id="searchType")
                    with gr.Row():
                        content_type = gr.Dropdown(label='Content type:', choices=content_choices, value=None, type="value", multiselect=True, elem_id="centerText")
                    with gr.Row():
                        base_filter = gr.Dropdown(label='Base model:', multiselect=True, choices=["SD 1.4", "SD 1.5", "SD 2.0", "SD 2.0 768", "SD 2.1", "SD 2.1 768", "SD 2.1 Unclip", "SXDXL 0.9", "SXDXL 1.0", "Other"], value=None, type="value", elem_id="centerText")
                    with gr.Row():
                        period_type = gr.Dropdown(label='Time period:', choices=["All Time", "Year", "Month", "Week", "Day"], value="All Time", type="value", elem_id="centerText")
                        sort_type = gr.Dropdown(label='Sort by:', choices=["Newest","Most Downloaded","Highest Rated","Most Liked"], value="Most Downloaded", type="value", elem_id="centerText")
                    with gr.Row(elem_id=component_id):
                        create_json = gr.Checkbox(label=f"Save tags after download", value=False, elem_id=toggle1, min_width=200)
                        toggle_date = gr.Checkbox(label="Divide cards by date", value=False, elem_id=toggle2, min_width=200)
                        show_nsfw = gr.Checkbox(label="NSFW content", value=False, elem_id=toggle3, min_width=200)
                    with gr.Row():
                        size_slider = gr.Slider(minimum=4, maximum=20, value=8, step=0.25, label='Tile size:')
                        tile_slider = gr.Slider(label="Tile count:", minimum=1, maximum=100, value=15, step=1, max_width=100)
                    with gr.Row(elem_id="save_set_box"):
                        save_settings = gr.Button(value="Save settings as default", elem_id="save_set_btn")
                search_term = gr.Textbox(label="", placeholder="Search CivitAI", elem_id="searchBox")
                refresh = gr.Button(label="", value="", elem_id=refreshbtn, icon="placeholder")
            with gr.Row(elem_id="pageBox"):
                get_prev_page = gr.Button(value="Prev page", interactive=False, elem_id="pageBtn1")
                page_slider = gr.Slider(label='Current page', step=1, minimum=1, maximum=1, value=1, min_width=80, elem_id="pageSlider")
                get_next_page = gr.Button(value="Next page", interactive=False, elem_id="pageBtn2")
            with gr.Row(elem_id="pageBoxMobile"):
                pass # Row used for button placement on mobile
            with gr.Row():
                list_html = gr.HTML(value='<div style="font-size: 24px; text-align: center; margin: 50px;">Click the search icon to load models.<br>Use the filter icon to filter results.</div>')
            with gr.Row():
                download_progress = gr.HTML(value='<div style="min-height: 0px;"></div>', elem_id="DownloadProgress")
            with gr.Row():
                list_models = gr.Dropdown(label="Model:", choices=[], interactive=False, elem_id="quicksettings1", value=None)
                list_versions = gr.Dropdown(label="Version:", choices=[], interactive=False, elem_id="quicksettings", value=None)
                file_list = gr.Dropdown(label="File:", choices=[], interactive=False, elem_id="file_list", value=None)
            with gr.Row():
                with gr.Column(scale=4):
                    install_path = gr.Textbox(label="Download folder:", interactive=False, max_lines=1)
                with gr.Column(scale=2):
                    sub_folder = gr.Dropdown(label="Sub folder:", choices=[], interactive=False, value=None)
            with gr.Row():
                with gr.Column(scale=4):
                    trained_tags = gr.Textbox(label='Trained tags (if any):', value=None, interactive=False, lines=1)
                with gr.Column(scale=2, elem_id="spanWidth"):
                    base_model = gr.Textbox(label='Base model:', value='', interactive=False, lines=1, elem_id="baseMdl")
                    model_filename = gr.Textbox(label="Model filename:", interactive=False, value=None)
            with gr.Row():
                save_tags = gr.Button(value="Save tags", interactive=False)
                save_images = gr.Button(value="Save images", interactive=False)
                download_model = gr.Button(value="Download model", interactive=False)
                cancel_model = gr.Button(value="Cancel download", interactive=False, visible=False)
                delete_model = gr.Button(value="Delete model", interactive=False, visible=False)
            with gr.Row():
                preview_html = gr.HTML(elem_id="civitai_preview_html")
            with gr.Row():
                back_to_top = gr.Button(value="Back to top", interactive=True, visible=False)
        with gr.Tab("Update Models"):
            with gr.Row():
                selected_tags = gr.CheckboxGroup(elem_id="selected_tags", label="Scan for:", choices=content_choices)
            with gr.Row():
                save_all_tags = gr.Button(value="Update assigned tags", interactive=True, visible=True)
                cancel_all_tags = gr.Button(value="Cancel updating tags", interactive=False, visible=False)
            with gr.Row():
                tag_progress = gr.HTML(value='<div style="min-height: 0px;"></div>')
            with gr.Row():
                ver_search = gr.Button(value="Scan for available updates", interactive=True, visible=True)
                cancel_ver_search = gr.Button(value="Cancel updates scan", interactive=False, visible=False)
                load_to_browser = gr.Button(value="Load outdated models to browser", interactive=False, visible=False)
            with gr.Row():
                version_progress = gr.HTML(value='<div style="min-height: 0px;"></div>')
            with gr.Row():
                load_installed = gr.Button(value="Load all installed models", interactive=True, visible=True)
                cancel_installed = gr.Button(value="Cancel loading models", interactive=False, visible=False)
                load_to_browser_installed = gr.Button(value="Load installed models to browser", interactive=False, visible=False)
            with gr.Row():
                installed_progress = gr.HTML(value='<div style="min-height: 0px;"></div>')
                
        #Invisible triggers/variables
        model_id = gr.Textbox(value=None, visible=False)
        dl_url = gr.Textbox(value=None, visible=False)
        event_text = gr.Textbox(elem_id="eventtext1", visible=False)
        download_start = gr.Textbox(value=None, visible=False)
        download_finish = gr.Textbox(value=None, visible=False)
        tag_start = gr.Textbox(value=None, visible=False)
        tag_finish = gr.Textbox(value=None, visible=False)
        ver_start = gr.Textbox(value=None, visible=False)
        ver_finish = gr.Textbox(value=None, visible=False)
        installed_start = gr.Textbox(value=None, visible=None)
        installed_finish = gr.Textbox(value=None, visible=None)
        delete_finish = gr.Textbox(value=None, visible=False)
        current_model = gr.Textbox(value=None, visible=False)
        current_sha256 = gr.Textbox(value=None, visible=False)
        
        # Global variable to detect if content has changed.
        def save_tags_btn(tags, file):
            if tags and file: btn = True
            else: btn = False
            return gr.Button.update(interactive=btn)
        
        def changeInput():
            gl.contentChange = True
        
        def ToggleDate(toggle_date):
            gl.sortNewest = toggle_date
        
        def update_tile_count(slider_value):
            gl.tile_count = slider_value
        
        def select_subfolder(sub_folder):
            if sub_folder == "None":
                newpath = gl.main_folder
            else:
                newpath = gl.main_folder + sub_folder
            return gr.Textbox.update(value=newpath)

        # Javascript Functions #
        back_to_top.click(
            fn=None,
            inputs=[],
            _js="() => BackToTop()"
        )
        
        page_slider.release(
            fn=None,
            inputs=[],
            _js="() => pressRefresh()"
        )
        
        download_finish.change(
            fn=None,
            inputs=[current_model],
            _js="(modelName) => updateCard(modelName)"
        )
        
        delete_finish.change(
            fn=None,
            inputs=[current_model],
            _js="(modelName) => updateCard(modelName)"
        )

        list_html.change(
            fn=None,
            inputs=[show_nsfw],
            _js="(hideAndBlur) => toggleNSFWContent(hideAndBlur)"
        )
        
        show_nsfw.change(
            fn=None,
            inputs=[show_nsfw],
            _js="(hideAndBlur) => toggleNSFWContent(hideAndBlur)"
        )
        
        list_html.change(
            fn=None,
            inputs=[size_slider],
            _js="(size) => updateCardSize(size, size * 1.5)"
        )

        size_slider.change(
            fn=None,
            inputs=[size_slider],
            _js="(size) => updateCardSize(size, size * 1.5)"
        )
        
        # Gradio components Logic #
        trained_tags.input(
            fn=save_tags_btn,
            inputs=[trained_tags, model_filename],
            outputs=[save_tags]
        )
        
        save_settings.click(
            fn=saveSettings,
            inputs=[
                use_search_term,
                content_type,
                period_type,
                sort_type,
                base_filter,
                create_json,
                toggle_date,
                show_nsfw,
                size_slider,
                tile_slider
            ]
        )
        
        toggle_date.input(
            fn=ToggleDate,
            inputs=[toggle_date]
        )
        
        tile_slider.release(
            fn=update_tile_count,
            inputs=[tile_slider],
            outputs=[]
        )
        
        content_type.change(
            fn=changeInput,
            inputs=[]
        )
        
        sub_folder.select(
            fn=select_subfolder,
            inputs=[sub_folder],
            outputs=[install_path]
        )
        
        ver_search.click(
            fn=_file.start_ver_search,
            inputs=[ver_start],
            outputs=[
                ver_start,
                ver_search,
                cancel_ver_search,
                load_installed,
                save_all_tags,
                version_progress
                ]
        )
        
        ver_start.change(
            fn=_file.file_scan,
            inputs=[
                selected_tags,
                ver_finish,
                tag_finish,
                installed_finish
                ],
            outputs=[
                version_progress,
                ver_finish
                ]
        )
        
        ver_finish.change(
            fn=_file.finish_ver_search,
            outputs=[
                ver_search,
                save_all_tags,
                load_installed,
                cancel_ver_search,
                load_to_browser
            ]
        )
        
        cancel_ver_search.click(
            fn=_file.cancel_scan
        )
        
        load_installed.click(
            fn=_file.start_installed_models,
            inputs=[installed_start],
            outputs=[
                installed_start,
                load_installed,
                cancel_installed,
                ver_search,
                save_all_tags,
                installed_progress
            ]
        )
        
        installed_start.change(
            fn=_file.file_scan,
            inputs=[
                selected_tags,
                ver_finish,
                tag_finish,
                installed_finish
                ],
            outputs=[
                installed_progress,
                installed_finish
            ]
        )
        
        installed_finish.change(
            fn=_file.finish_installed_models,
            outputs=[
                ver_search,
                save_all_tags,
                load_installed,
                cancel_installed,
                load_to_browser_installed
            ]
        )
        
        load_to_browser_installed.click(
            fn=_file.load_to_browser,
            outputs=[
                ver_search,
                save_all_tags,
                load_installed,
                cancel_installed,
                load_to_browser_installed,
                list_models,
                list_versions,
                list_html,
                get_prev_page,
                get_next_page,
                page_slider,
                save_tags,
                save_images,
                download_model,
                install_path,
                sub_folder,
                file_list,
                back_to_top,
                installed_progress
            ]
        )
        
        load_to_browser.click(
            fn=_file.load_to_browser,
            outputs=[
                ver_search,
                save_all_tags,
                load_installed,
                cancel_ver_search,
                load_to_browser,
                list_models,
                list_versions,
                list_html,
                get_prev_page,
                get_next_page,
                page_slider,
                save_tags,
                save_images,
                download_model,
                install_path,
                sub_folder,
                file_list,
                back_to_top,
                version_progress
            ]
        )
        
        save_all_tags.click(
            fn=_file.save_tag_start,
            inputs=[tag_start],
            outputs=[
                tag_start,
                save_all_tags,
                cancel_all_tags,
                load_installed,
                ver_search,
                tag_progress
            ]
        )
        
        tag_start.change(
            fn=_file.file_scan,
            inputs=[
                selected_tags,
                ver_finish,
                tag_finish,
                installed_finish
                ],
            outputs=[
                tag_progress,
                tag_finish
            ]
        )
        
        tag_finish.change(
            fn=_file.save_tag_finish,
            outputs=[
                ver_search,
                save_all_tags,
                load_installed,
                cancel_all_tags
            ]
        )
        
        cancel_all_tags.click(
            fn=_file.cancel_scan
        )
        
        model_filename.change(
            fn=insert_sub,
            inputs=[
                list_models,
                list_versions
                ],
            outputs=[sub_folder]
        )
        
        download_model.click(
            fn=_download.download_start,
            inputs=[
                download_start,
                list_models,
                model_filename,
                list_versions,
                current_sha256,
                model_id
                ],
            outputs=[
                download_model,
                cancel_model,
                download_start,
                download_progress
            ]
        )
        
        download_start.change(
            fn=_download.download_create_thread,
            inputs=[
                download_finish,
                dl_url,
                model_filename,
                preview_html,
                create_json,
                trained_tags,
                install_path,
                list_models,
                list_versions
                ],
            outputs=[
                download_progress,
                current_model,
                download_finish
            ]
        )
        
        cancel_model.click(
            fn=_download.download_cancel,
            inputs=[
                delete_finish,
                list_models,
                list_versions,
                model_filename,
                current_sha256
                ],
            outputs=[
                download_model,
                cancel_model,
                download_progress
            ]
        )
        
        download_finish.change(
            fn=_download.download_finish,
            inputs=[
                model_filename,
                list_versions,
                list_models
                ],
            outputs=[
                download_model,
                cancel_model,
                delete_model,
                download_progress,
                list_versions
            ]
        )
        
        delete_model.click(
            fn=_file.delete_model,
            inputs=[
                delete_finish,
                model_filename,
                list_models,
                list_versions,
                current_sha256
                ],
            outputs=[
                download_model,
                cancel_model,
                delete_model,
                delete_finish,
                current_model,
                list_versions
            ]
        )
        
        save_tags.click(
            fn=_file.save_json,
            inputs=[
                model_filename,
                install_path,
                trained_tags
                ],
            outputs=[trained_tags]
        )
        
        save_images.click(
            fn=_file.save_images,
            inputs=[
                preview_html,
                model_filename,
                list_models,
                install_path
                ],
            outputs=[]
        )
        
        list_models.select(
            fn=_api.update_model_versions,
            inputs=[
                list_models
            ],
            outputs=[
                list_versions,
                back_to_top
            ]
        )
        
        list_versions.change(
            fn=_api.update_model_info,
            inputs=[
                list_models,
                list_versions
                ],
            outputs=[
                preview_html,
                trained_tags,
                base_model,
                download_model,
                delete_model,
                file_list,
                model_filename,
                model_id,
                current_sha256,
                install_path,
                sub_folder
            ]
        )
        
        file_list.input(
            fn=_api.update_file_info,
            inputs=[
                list_models,
                list_versions,
                file_list
            ],
            outputs=[
                model_filename,
                model_id,
                current_sha256,
                download_model,
                delete_model,
                install_path,
                sub_folder
            ]
        )
        
        model_id.change(
            fn=_api.update_dl_url,
            inputs=[
                trained_tags,
                model_id,
                list_models,
                list_versions
                ],
            outputs=[
                dl_url,
                save_tags,
                save_images,
                download_model
                ]
        )
        
        # Define common page load inputs
        common_inputs = [
            content_type,
            sort_type,
            period_type,
            use_search_term,
            search_term,
            page_slider,
            base_filter
        ]
        
        # Define common page load outputs
        common_outputs = [
            list_models,
            list_versions,
            list_html,
            get_prev_page,
            get_next_page,
            page_slider,
            save_tags,
            save_images,
            download_model,
            install_path,
            sub_folder,
            file_list,
            back_to_top
        ]

        # Map triggers to their corresponding functions
        trigger_function_map = {
            refresh.click: _api.update_model_list,
            search_term.submit: _api.update_model_list,
            get_next_page.click: _api.update_next_page,
            get_prev_page.click: _api.update_prev_page
        }

        # Loop through the dictionary and bind each trigger to its function
        for trigger, function in trigger_function_map.items():
            trigger(fn=function, inputs=common_inputs, outputs=common_outputs)
        
        def update_models_dropdown(model_name):
            model_name = re.sub(r'\.\d{3}$', '', model_name)
            (ret_versions, back_to_top) = _api.update_model_versions(model_name)
            (html, tags, _, DwnButton, _, filelist, filename, id, current_sha256, install_path, sub_folder) = _api.update_model_info(model_name,ret_versions['value'])
            (dl_url, _, _, _) = _api.update_dl_url(tags, id['value'], model_name, ret_versions['value'])
            return  gr.Dropdown.update(value=model_name),ret_versions,html,dl_url,tags,filename,install_path,sub_folder,DwnButton,filelist,id,current_sha256,back_to_top
        
        event_text.change(
            fn=update_models_dropdown,
            inputs=[
                event_text
                ],
            outputs=[
                list_models,
                list_versions,
                preview_html,
                dl_url,
                trained_tags,
                model_filename,
                install_path,
                sub_folder,
                download_model,
                file_list,
                model_id,
                current_sha256,
                back_to_top
            ]
        )

    return (civitai_interface, "Civit AI", "civitai_interface"),

def on_ui_settings():
    section = ("civitai_browser_plus", "Civit AI")

    if not (hasattr(shared.OptionInfo, "info") and callable(getattr(shared.OptionInfo, "info"))):
        def info(self, info):
            self.label += f" ({info})"
            return self
        shared.OptionInfo.info = info
    
    shared.opts.add_option("use_aria2", shared.OptionInfo(True, "Download models using Aria2", section=section).info("Disable to use the old download method"))
    shared.opts.add_option("disable_dns", shared.OptionInfo(False, "Disable Async DNS for Aria2", section=section).info("Useful for users who use PortMaster or other software that controls the DNS"))
    shared.opts.add_option("show_log", shared.OptionInfo(False, "Show Aria2 Logs in CMD", section=section).info("Requires Web-UI Restart"))
    shared.opts.add_option("split_aria2", shared.OptionInfo(64, "Number of connections to use for downloading a model", gr.Slider, lambda: {"maximum": "64", "minimum": "1", "step": "1"}, section=section).info("Only applies to Aria2"))
    shared.opts.add_option("insert_sub", shared.OptionInfo(True, "Insert [/Model Name] & [/Model Name/Version Name] as default sub folder options", section=section))
    shared.opts.add_option("use_LORA", shared.OptionInfo(False, "Treat LoCon's as LORA's", section=section).info("SD-Panel v1.5 and higher treats LoCON's the same as LORA's, so they can be placed in the LORA folder."))
    shared.opts.add_option("unpack_zip", shared.OptionInfo(False, "Automatically unpack .zip after downloading", section=section))
    
script_callbacks.on_ui_tabs(on_ui_tabs)
script_callbacks.on_ui_settings(on_ui_settings)
