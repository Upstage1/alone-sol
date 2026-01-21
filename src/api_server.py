from flask import Flask, jsonify, render_template, request, Response
import logging
from typing import Optional, Dict, Any
import json
import os

logger = logging.getLogger(__name__)

class APIServer:
    """Flask REST API server for the pump.fun bot"""
    
    def __init__(self, bot_core=None):
        template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), './site')
        self.app = Flask(__name__, template_folder=template_folder)
        self.bot_core = bot_core
        self._setup_routes()
    
    def _serve_js_file(self, filename: str) -> Response:
        """Serve JavaScript file with proper content type"""
        try:
            if filename.endswith('.js'):
                mimetype = 'application/javascript'
                content_type = 'application/javascript; charset=utf-8'
            elif filename.endswith('.css'):
                mimetype = 'text/css'
                content_type = 'text/css; charset=utf-8'
            else:
                # По умолчанию пустой ответ с типом text/plain
                mimetype = 'text/plain'
                content_type = 'text/plain; charset=utf-8'

            if filename.find(".js"):
                path_file = os.path.join(os.path.dirname(__file__), 'site', filename)
                # path_file = os.path.join('../site', filename)

            elif filename.find(".css"):
                path_file = os.path.join(os.path.dirname(__file__), 'site', filename)
                # path_file = os.path.join('../site', filename)

            else:
                # Если файл не найден, возвращаем заглушку
                logger.warning(f"JS file not found: {filename}, returning default script")
                return Response(
                    # self._get_default_js(filename),
                    "",
                    mimetype=mimetype,
                    headers={
                        'Cache-Control': 'public, max-age=3600',  # Кэширование на 1 час
                        'Content-Type': content_type
                    }
                )

            print("FILE:", path_file, os.path.exists(path_file))
            if os.path.exists(path_file):
                with open(path_file, 'r', encoding='utf-8') as f:
                    file__content = f.read()

                return Response(
                    file__content,
                    mimetype=mimetype,
                    headers={
                        'Cache-Control': 'public, max-age=3600',  # Кэширование на 1 час
                        'Content-Type': content_type
                    }
                )
            
            else:
                # Если файл не найден, возвращаем заглушку
                logger.warning(f"JS file not found: {filename}, returning default script")
                return Response(
                    # self._get_default_js(filename),
                    "",
                    mimetype=mimetype,
                    headers={'Content-Type': content_type}
                )

        except Exception as e:
            logger.error(f"Error serving JS file {filename}: {e}")
            return Response(
                f"// Error loading {filename}: {str(e)}\nconsole.error('Failed to load {filename}');",
                mimetype=mimetype,
                status=500
            )

    def _serve_static_file(self, filename: str) -> Response:
        """Serve static file (js, css, images, video) with proper content type."""
        import mimetypes

        # Список поддерживаемых расширений
        extensions = {
            '.js':  'application/javascript; charset=utf-8',
            '.css': 'text/css; charset=utf-8',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
            '.mp4': 'video/mp4'
        }

        # Находим расширение
        ext = os.path.splitext(filename)[1].lower()
        content_type = extensions.get(ext) or mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        # Для текстовых - режим r, для бинарных - rb
        is_binary = ext in ['.png', '.jpg', '.jpeg', '.webp', '.mp4']

        # Формируем путь к файлу
        static_folder = os.path.join(os.path.dirname(__file__), 'site')
        path_file = os.path.join(static_folder, filename)

        try:
            if os.path.exists(path_file):
                with open(path_file, 'rb' if is_binary else 'r', encoding=None if is_binary else 'utf-8') as f:
                    file_content = f.read()
                return Response(
                    file_content,
                    mimetype=content_type,
                    headers={
                        'Cache-Control': 'public, max-age=3600',
                        'Content-Type': content_type
                    }
                )
            else:
                logger.warning(f"Static file not found: {filename}")
                return Response(
                    b'' if is_binary else '',
                    mimetype=content_type,
                    status=404,
                    headers={'Content-Type': content_type}
                )
        except Exception as e:
            logger.error(f"Error serving static file {filename}: {e}")
            return Response(
                (f"// Error loading {filename}: {str(e)}" if not is_binary else b""),
                mimetype=content_type,
                status=500,
                headers={'Content-Type': content_type}
            )

    def _setup_routes(self):
        """Setup all API routes"""
        
        @self.app.route('/')
        def index():
            """Serve the main dashboard"""
            # Теперь используем render_template для загрузки index.html из папки ./site/
            return render_template('index.html')
        
        @self.app.route('/control')
        def control_panel():
            """Serve the main dashboard"""
            return render_template('control.index.html')
        
        @self.app.route('/api/status')
        def get_status():
            """Get bot status"""
            try:
                if self.bot_core:
                    status = self.bot_core.get_status()
                    return jsonify({
                        'success': True,
                        'mode': self.bot_core.mode,
                        'data': status
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Bot not initialized'
                    })
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/messages')
        def get_messages():
            """Get recent chat messages"""
            try:
                limit = request.args.get('limit', 50, type=int)
                if self.bot_core:
                    messages = self.bot_core.get_recent_messages(limit)
                    return jsonify({
                        'success': True,
                        'data': {
                            'messages': messages,
                            'count': len(messages)
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Bot not initialized'
                    })
            except Exception as e:
                logger.error(f"Error getting messages: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/analysis')
        def get_analysis():
            """Get ChatGPT analysis results"""
            try:
                limit = request.args.get('limit', 10, type=int)
                if self.bot_core:
                    analyses = self.bot_core.get_analysis_results(limit)
                    latest = self.bot_core.get_latest_analysis()
                    return jsonify({
                        'success': True,
                        'data': {
                            'analyses': analyses,
                            'latest': latest,
                            'count': len(analyses)
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Bot not initialized'
                    })
            except Exception as e:
                logger.error(f"Error getting analysis: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/statistics')
        def get_statistics():
            """Get detailed statistics"""
            try:
                if self.bot_core:
                    stats = self.bot_core.get_statistics()
                    return jsonify({
                        'success': True,
                        'data': stats
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Bot not initialized'
                    })
            except Exception as e:
                logger.error(f"Error getting statistics: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': self._get_timestamp()
            })
        
        @self.app.route('/api/pause', methods=['POST'])
        def pause_bot():
            """Pause the bot"""
            try:
                if self.bot_core:
                    self.bot_core.pause()
                    return jsonify({
                        'success': True,
                        'message': 'Bot paused successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Bot not initialized'
                    })
            except Exception as e:
                logger.error(f"Error pausing bot: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/resume', methods=['POST'])
        def resume_bot():
            """Resume the bot"""
            try:
                if self.bot_core:
                    self.bot_core.resume()
                    return jsonify({
                        'success': True,
                        'message': 'Bot resumed successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Bot not initialized'
                    })
            except Exception as e:
                logger.error(f"Error resuming bot: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
            
        @self.app.route('/api/mode', methods=['POST'])
        def mode_bot():
            """Mode the bot"""
            try:
                if request.is_json:
                    mode = request.json.get('mode', False)
                    self.bot_core._change_mode(mode)
                    return jsonify({
                        'success': True,
                        'message': 'Mode change successfully: ' + mode
                    })

                else:
                    return jsonify({
                        'success': False,
                        'message': 'Error: not find mode'
                    }), 500
                
            except Exception as e:
                logger.error(f"Error mode bot: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/css/<path:filename>')
        def serve_css_file(filename):
            """Serve any CSS file from the css directory (site/css/...)"""
            return self._serve_static_file(os.path.join('css', filename))

        @self.app.route('/js/<path:filename>')
        def serve_main_js(filename):
            """Serve script.js file"""
            return self._serve_static_file(os.path.join('js', filename))
        
        @self.app.route('/img/<path:filename>')
        def serve_static(filename):
            """Serve static and media files by extension"""
            return self._serve_static_file(os.path.join('img', filename))

        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'success': False,
                'error': 'Endpoint not found'
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Run the Flask server"""
        logger.info(f"Starting Flask server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)