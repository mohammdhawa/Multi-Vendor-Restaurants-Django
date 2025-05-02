def detect_user(user):
    redirect_url = ''
    if user.role == 1:
        redirect_url = 'vendor-dashboard'
    elif user.role == 2:
        redirect_url = 'customer-dashboard'
    elif user.role == None and user.is_superadmin:
        redirect_url = '/admin'

    return redirect_url
