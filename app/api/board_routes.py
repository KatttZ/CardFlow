from flask import Blueprint,request,jsonify
from flask_login import login_required, current_user
from app.models import db, Board, List


board_routes = Blueprint('boards', __name__)


@board_routes.route('/', methods=['GET'])
@login_required
def get_user_boards():
    """
    Get all boards for current user
    """
    boards = Board.query.filter(Board.user_id == current_user.id).all()
    if not boards:
        return {'boards':[], 'message': 'No boards found'}
    return {'boards': [board.to_dict() for board in boards], 'count': len(boards)}



@board_routes.route('/', methods=['POST'])
@login_required
def create_board():
    """
    Create a new board
    """
    data = request.get_json()
    if 'title' not in data:
        return {'errors': 'Title is required'}, 400
    
    new_board = Board(
        title=data['title'],
        user_id=current_user.id
    )
    db.session.add(new_board)
    db.session.commit()
    return new_board.to_dict()


@board_routes.route('/<int:board_id>', methods=['GET'])
@login_required
def get_board(board_id):
    """
    Get a specific board by id
    """
    board = Board.query.get(board_id)
    if not board:
        return {'errors': 'Board not found'}, 404
    if board.user_id != current_user.id:
        return {'errors': 'Unauthorized'}, 401
    
    return board.to_dict(include_lists=True)


@board_routes.route('/<int:board_id>', methods=['PUT'])
@login_required
def update_board(board_id):
    """
    Update a specific board by id
    """
    board = Board.query.get(board_id)
    if not board:
        return {'errors': 'Board not found'}, 404
    if board.user_id != current_user.id:
        return {'errors': 'Unauthorized'}, 401

    data = request.get_json()
    if 'title' not in data:
        return {'errors': 'Title is required'}, 400
    board.title = data['title']
    db.session.commit()
    return board.to_dict()


@board_routes.route('/<int:board_id>', methods=['DELETE'])
@login_required
def delete_board(board_id):
    """
    Delete a specific board by id
    """
    board = Board.query.get(board_id)
    if not board:
        return {'errors': 'Board not found'}, 404
    if board.user_id != current_user.id:
        return {'errors': 'Unauthorized'}, 401

    db.session.delete(board)
    db.session.commit()
    return {'message': 'Board deleted'}

@board_routes.route('/search', methods=['GET'])
@login_required
def search_boards():
    """
    Search for boards by title
    """
    query = request.args.get('query','')
    if not query:
        return jsonify([])
    boards = Board.query.filter(Board.user_id == current_user.id, Board.title.ilike(f'%{query}%')).all()

    if not boards:
        return {'boards': [], 'message': 'No boards found'}
    return {'boards': [board.to_dict() for board in boards]}


#================================Lists related routes==============================

@board_routes.route('/<int:board_id>/lists', methods=['GET'])
@login_required
def get_board_lists(board_id):
    """
    Get all lists in a board
    """
    board = Board.query.get(board_id)
    if not board:
        return {'errors': 'Board not found'}, 404
    if board.user_id != current_user.id:
        return {'errors': 'Unauthorized'}, 401
    
    lists = List.query.filter(List.board_id == board_id).order_by(List.position).all()

    return {'lists': [list.to_dict() for list in lists]}


@board_routes.route('/<int:board_id>/lists', methods=['POST'])
@login_required
def create_list(board_id):
    """
    Create a new list in a board
    """
    board = Board.query.get(board_id)
    if not board:
        return {'errors': 'Board not found'}, 404
    if board.user_id != current_user.id:
        return {'errors': 'Unauthorized'}, 401

    data = request.get_json()
    if 'title' not in data:
        return {'errors': 'Title is required'}, 400
    
    existing_lists = List.query.filter(List.board_id == board_id).all()
    desired_position = data.get('position')
    if desired_position is not None:
        for list in existing_lists:
            if list.position >= desired_position:
                list.position += 1
    else:
        desired_position = len(existing_lists) + 1

    new_list = List(
        title=data['title'],
        board_id=board_id,
        position=desired_position
    )
    
    db.session.add(new_list)
    db.session.commit()
    return new_list.to_dict()


@board_routes.route('/<int:board_id>/lists/reorder', methods=['PUT'])
@login_required
def reorder_lists(board_id):
    """
    Reorder lists within a board
    """
    board = Board.query.get(board_id)
    if not board:
        return {'errors': 'Board not found'}, 404
    if board.user_id != current_user.id:
        return {'errors': 'Unauthorized'}, 401

    data = request.get_json()
    reordered_list_ids = data.get('reorderedLists')
    if not reordered_list_ids:
        return {'errors': 'No reordered list IDs provided'}, 400

    # Update the position of each list
    for position, list_id in enumerate(reordered_list_ids, start=1):
        list_obj = List.query.get(list_id)
        if list_obj and list_obj.board_id == board_id:
            list_obj.position = position

    db.session.commit()

    # Return the updated lists
    lists = List.query.filter(List.board_id == board_id).order_by(List.position).all()
    return {'lists': [list.to_dict() for list in lists]}
