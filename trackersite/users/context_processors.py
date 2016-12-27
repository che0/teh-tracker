from models import UserWrapper

def wrapped_user(request):
    return {'wrapped_user': UserWrapper(request.user)}
