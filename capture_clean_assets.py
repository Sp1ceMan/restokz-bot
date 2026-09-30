import http.server
import socketserver
import threading
import subprocess
import os
import time
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PORT = 8977

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def run_server():
    httpd = socketserver.TCPServer(('127.0.0.1', PORT), QuietHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd

def capture_clean_mobile(url_path, output_filename, wait_sec=1):
    edge = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    
    # HTML wrapper with iframe ensuring exact 412x892 viewport without clipping or scrollbars
    wrapper_html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    background: #0E1013;
    width: 600px;
    height: 1050px;
    overflow: hidden;
  }}
  iframe {{
    width: 412px;
    height: 892px;
    border: none;
    overflow: hidden;
    display: block;
  }}
</style>
</head>
<body>
  <iframe id="appFrame" scrolling="no" src="http://127.0.0.1:{PORT}/{url_path}"></iframe>
</body>
</html>'''

    temp_html = f'temp_frame_{output_filename}.html'
    with open(temp_html, 'w', encoding='utf-8') as f:
        f.write(wrapper_html)
    
    temp_canvas = os.path.abspath(f'temp_canvas_{output_filename}.png')
    
    subprocess.run([
        edge,
        '--headless=new',
        '--disable-gpu',
        '--hide-scrollbars',
        '--window-size=600,1050',
        f'--screenshot={temp_canvas}',
        f'http://127.0.0.1:{PORT}/{temp_html}'
    ], timeout=20)
    
    if os.path.exists(temp_html):
        try: os.remove(temp_html)
        except: pass
        
    if os.path.exists(temp_canvas):
        canvas = Image.open(temp_canvas)
        # Crop exactly 412 x 892
        cropped = canvas.crop((0, 0, 412, 892))
        dest = os.path.join(r'd:\bot\presentation_assets', output_filename)
        cropped.save(dest, 'PNG')
        try: os.remove(temp_canvas)
        except: pass
        print(f'Successfully captured {output_filename}: {cropped.size}')
        return dest
    else:
        print(f'Failed to capture {output_filename}')
        return None

def main():
    print('Starting capture server...')
    httpd = run_server()
    time.sleep(1)
    
    tasks = [
        ('admin.html', 'admin_terminal_mobile.png'),
        ('index.html', 'guest_catalog_mobile.png'),
        ('index.html?rest=1', 'guest_restaurant_modal.png'),
        ('admin.html?tab=floor', 'admin_floor_map.png'),
        ('admin.html?open=shift', 'admin_shift_modal.png'),
        ('admin.html?open=picker', 'admin_rest_picker.png'),
        ('admin.html?open=drawer', 'admin_drawer_menu.png'),
    ]
    
    for url, filename in tasks:
        print(f'Capturing {filename} from {url}...')
        capture_clean_mobile(url, filename)
        
    httpd.shutdown()
    print('All mobile assets captured cleanly without clipping!')

if __name__ == '__main__':
    main()
