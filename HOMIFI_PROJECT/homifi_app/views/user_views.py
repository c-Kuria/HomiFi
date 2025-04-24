from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import User, LinkedAccount
from ..forms import UserRegistrationForm, UserProfileForm
from django.db.models import Q

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, 'Registration successful!')
                return redirect('homifi_app:index')
            except Exception as e:
                form.add_error(None, str(e))
        else:
            pass
    else:
        form = UserRegistrationForm()
    return render(request, 'auth/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            # Handle profile picture removal
            if request.POST.get('remove_picture') == 'true' and request.user.profile_picture:
                # Delete the old file
                request.user.profile_picture.delete(save=False)
                # Clear the field
                request.user.profile_picture = None
            
            user = form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('homifi_app:profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'auth/profile.html', {'form': form})

@login_required
def create_linked_account(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            secondary_user = User.objects.get(email=email)
            if secondary_user != request.user:
                LinkedAccount.objects.create(
                    primary_user=request.user,
                    secondary_user=secondary_user
                )
                messages.success(request, 'Account linked successfully!')
            else:
                messages.error(request, 'You cannot link your own account.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    return redirect('homifi_app:manage_accounts')

@login_required
def switch_account(request, account_id):
    try:
        linked_account = LinkedAccount.objects.get(
            id=account_id,
            primary_user=request.user
        )
        # Store current user's session data
        request.session['original_user_id'] = request.user.id
        # Switch to secondary account
        login(request, linked_account.secondary_user)
        messages.success(request, f'Switched to {linked_account.secondary_user.username}\'s account')
    except LinkedAccount.DoesNotExist:
        messages.error(request, 'Invalid account link.')
    return redirect('homifi_app:dashboard')

@login_required
def manage_accounts(request):
    # Get all linked accounts where user is either primary or secondary
    linked_accounts = LinkedAccount.objects.filter(
        Q(primary_user=request.user) | Q(secondary_user=request.user)
    ).select_related('primary_user', 'secondary_user')
    
    return render(request, 'auth/manage_accounts.html', {
        'linked_accounts': linked_accounts
    }) 