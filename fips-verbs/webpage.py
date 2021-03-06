"""fips verb to build the oryol samples webpage"""

import os
import yaml 
import shutil
import subprocess
import glob
from string import Template

from mod import log, util, project, emscripten, android

GitHubSamplesURL = 'https://github.com/floooh/oryol-samples/tree/master/src/'

BuildEmscripten = True
BuildWasm = True
ExportAssets = True

EmscConfig = 'webgl2-emsc-ninja-release'
WasmConfig = 'webgl2-wasm-ninja-release'

#-------------------------------------------------------------------------------
def deploy_webpage(fips_dir, proj_dir, webpage_dir) :
    """builds the final webpage under under fips-deploy/oryol-samples-webpage"""
    ws_dir = util.get_workspace_dir(fips_dir)

    # load the websamples.yml file, should have been created during the last build
    with open(webpage_dir + '/websamples.yml', 'r') as f :
        samples = yaml.load(f.read())

    # create directories
    for platform in ['asmjs', 'wasm'] :
        platform_dir = '{}/{}'.format(webpage_dir, platform)
        if not os.path.isdir(platform_dir) :
            os.makedirs(platform_dir)

    # link to the Core Samples
    content  = '<div class="thumb">\n'
    content += '  <div class="thumb-title">To Core Samples...</div>\n'
    content += '  <div class="img-frame"><a href="http://floooh.github.com/oryol/index.html"><img class="image" src="core_samples.jpg"></img></a></div>\n'
    content += '</div>\n'

    # build the thumbnail gallery
    for sample in samples :
        if sample['name'] != '__end__' :
            name    = sample['name']
            imgPath = sample['image']
            types   = sample['type'] 
            desc    = sample['desc']
            head, tail = os.path.split(imgPath)
            if tail == 'none' :
                imgFileName = 'dummy.jpg'
            else :
                imgFileName = tail
            content += '<div class="thumb">\n'
            content += '  <div class="thumb-title">{}</div>\n'.format(name)
            content += '  <div class="img-frame"><a href="asmjs/{}.html"><img class="image" src="{}" title="{}"></img></a></div>\n'.format(name,imgFileName,desc)
            content += '  <div class="thumb-bar">\n'
            content += '    <ul class="thumb-list">\n'
            if BuildEmscripten and 'emscripten' in types :
                content += '      <li class="thumb-item"><a class="thumb-link" href="asmjs/{}.html">asm.js</a></li>\n'.format(name)
            if BuildWasm and 'emscripten' in types :
                content += '      <li class="thumb-item"><a class="thumb-link" href="wasm/{}.html">wasm</a></li>\n'.format(name)
            content += '    </ul>\n'
            content += '  </div>\n'
            content += '</div>\n'

    # populate the html template, and write to the build directory
    with open(proj_dir + '/web/index.html', 'r') as f :
        templ = Template(f.read())
    html = templ.safe_substitute(samples=content)
    with open(webpage_dir + '/index.html', 'w') as f :
        f.write(html)

    # copy other required files
    for name in ['style.css', 'dummy.jpg', 'emsc.js', 'wasm.js', 'about.html', 'favicon.png', 'core_samples.jpg'] :
        log.info('> copy file: {}'.format(name))
        shutil.copy(proj_dir + '/web/' + name, webpage_dir + '/' + name)

    # generate emscripten HTML pages
    if BuildEmscripten and emscripten.check_exists(fips_dir) :
        emsc_deploy_dir = '{}/fips-deploy/oryol-samples/{}'.format(ws_dir, EmscConfig)
        for sample in samples :
            name = sample['name']
            if name != '__end__' and 'emscripten' in sample['type'] :
                log.info('> generate emscripten HTML page: {}'.format(name))
                for ext in ['js', 'html.mem'] :
                    src_path = '{}/{}.{}'.format(emsc_deploy_dir, name, ext)
                    if os.path.isfile(src_path) :
                        shutil.copy(src_path, '{}/asmjs/'.format(webpage_dir))
                with open(proj_dir + '/web/emsc.html', 'r') as f :
                    templ = Template(f.read())
                src_url = GitHubSamplesURL + sample['src'];
                html = templ.safe_substitute(name=name, source=src_url)
                with open('{}/asmjs/{}.html'.format(webpage_dir, name, name), 'w') as f :
                    f.write(html)

    # generate WebAssembly HTML pages
    if BuildWasm and emscripten.check_exists(fips_dir) :
        wasm_deploy_dir = '{}/fips-deploy/oryol-samples/{}'.format(ws_dir, WasmConfig)
        for sample in samples :
            name = sample['name']
            if name != '__end__' and 'emscripten' in sample['type'] :
                log.info('> generate wasm HTML page: {}'.format(name))
                for ext in ['js', 'wasm.mappedGlobals'] :
                    src_path = '{}/{}.{}'.format(wasm_deploy_dir, name, ext)
                    if os.path.isfile(src_path) :
                        shutil.copy(src_path, '{}/wasm/'.format(webpage_dir))
                for ext in ['html.mem', 'wasm'] :
                    src_path = '{}/{}.{}'.format(wasm_deploy_dir, name, ext)
                    if os.path.isfile(src_path) :
                        shutil.copy(src_path, '{}/wasm/{}.{}.txt'.format(webpage_dir, name, ext))
                with open(proj_dir + '/web/wasm.html', 'r') as f :
                    templ = Template(f.read())
                src_url = GitHubSamplesURL + sample['src'];
                html = templ.safe_substitute(name=name, source=src_url)
                with open('{}/wasm/{}.html'.format(webpage_dir, name), 'w') as f :
                    f.write(html)

    # copy the screenshots
    for sample in samples :
        if sample['name'] != '__end__' :
            img_path = sample['image']
            head, tail = os.path.split(img_path)
            if tail != 'none' :
                log.info('> copy screenshot: {}'.format(tail))
                shutil.copy(img_path, webpage_dir + '/' + tail)

#-------------------------------------------------------------------------------
def export_assets(fips_dir, proj_dir, webpage_dir) :
    data_src_dir = '{}/data/'.format(proj_dir)
    data_dst_dir = '{}/data/'.format(webpage_dir)
    if not os.path.exists(data_dst_dir) :
        os.makedirs(data_dst_dir)
    for ext in ['txt', 'dump', 'kcc', 'tap', 'orb'] :
        for data_file in glob.glob('{}/*.{}'.format(data_src_dir, ext)) :
            shutil.copy(data_file, data_dst_dir)
    tbui_from = '{}/tbui'.format(data_src_dir)
    tbui_to   = '{}/tbui'.format(data_dst_dir)
    shutil.copytree(tbui_from, tbui_to)
    nkui_from = '{}/nkui'.format(data_src_dir)
    nkui_to   = '{}/nkui'.format(data_dst_dir)
    shutil.copytree(nkui_from, nkui_to)

#-------------------------------------------------------------------------------
def build_deploy_webpage(fips_dir, proj_dir) :
    # if webpage dir exists, clear it first
    ws_dir = util.get_workspace_dir(fips_dir)
    webpage_dir = '{}/fips-deploy/oryol-samples-webpage'.format(ws_dir)
    if os.path.isdir(webpage_dir) :
        shutil.rmtree(webpage_dir)
    os.makedirs(webpage_dir)

    if BuildEmscripten and emscripten.check_exists(fips_dir) :
        project.gen(fips_dir, proj_dir, EmscConfig)
        project.build(fips_dir, proj_dir, EmscConfig)
    if BuildWasm and emscripten.check_exists(fips_dir) :
        project.gen(fips_dir, proj_dir, WasmConfig)
        project.build(fips_dir, proj_dir, WasmConfig)
    
    # export sample assets
    if ExportAssets :
        export_assets(fips_dir, proj_dir, webpage_dir)

    # deploy the webpage
    deploy_webpage(fips_dir, proj_dir, webpage_dir)

    log.colored(log.GREEN, 'Generated Samples web page under {}.'.format(webpage_dir))

#-------------------------------------------------------------------------------
def serve_webpage(fips_dir, proj_dir) :
    ws_dir = util.get_workspace_dir(fips_dir)
    webpage_dir = '{}/fips-deploy/oryol-samples-webpage'.format(ws_dir)
    p = util.get_host_platform()
    if p == 'osx' :
        try :
            subprocess.call(
                'open http://localhost:8000 ; python {}/mod/httpserver.py'.format(fips_dir),
                cwd = webpage_dir, shell=True)
        except KeyboardInterrupt :
            pass
    elif p == 'win':
        try:
            subprocess.call(
                'cmd /c start http://localhost:8000 && python {}/mod/httpserver.py'.format(fips_dir),
                cwd = webpage_dir, shell=True)
        except KeyboardInterrupt:
            pass
    elif p == 'linux':
        try:
            subprocess.call(
                'xdg-open http://localhost:8000; python {}/mod/httpserver.py'.format(fips_dir),
                cwd = webpage_dir, shell=True)
        except KeyboardInterrupt:
            pass

#-------------------------------------------------------------------------------
def run(fips_dir, proj_dir, args) :
    if len(args) > 0 :
        if args[0] == 'build' :
            build_deploy_webpage(fips_dir, proj_dir)
        elif args[0] == 'serve' :
            serve_webpage(fips_dir, proj_dir)
        else :
            log.error("Invalid param '{}', expected 'build' or 'serve'".format(args[0]))
    else :
        log.error("Param 'build' or 'serve' expected")

#-------------------------------------------------------------------------------
def help() :
    log.info(log.YELLOW +
             'fips webpage build\n' +
             'fips webpage serve\n' +
             log.DEF +
             '    build oryol samples webpage')

