from flask import Blueprint, render_template, jsonify, request
from app.logic import get_directions

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Render the main search + map page
    return render_template('index.html')

@bp.route('/api/test')
def test():
    directions = get_directions("room_101", "room_102")
    return jsonify(directions)

@bp.route('/directions', methods=['POST'])
def directions():
    entrance = request.args.get('entrance')
    destination = request.args.get('destination')
    if not entrance or not destination:
        return jsonify({'error': 'Missing start or end parameter'}), 400
    result = get_directions(entrance, destination)
    if result == "No path found":
        return jsonify({'error': 'No path found'}), 404
    steps, coordinates = result
    return jsonify({'directions': steps, 'coordinates': coordinates})