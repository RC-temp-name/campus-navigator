from flask import Blueprint, render_template, jsonify, request
from app.logic import get_directions

bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET', 'POST'])
def index():
    steps = None
    coordinates = None
    error = None
    if request.method == 'POST':
        entrance = request.form.get('entrance')
        destination = request.form.get('destination')
        result = get_directions(entrance, destination)
        if result == "No path found":
            error = "No path found"
        else:
            steps, coordinates = result
    return render_template('index.html', steps=steps, coordinates=coordinates, error=error)

@bp.route('/api/test')
def test():
    directions = get_directions("room_101", "room_102")
    return jsonify(directions)
