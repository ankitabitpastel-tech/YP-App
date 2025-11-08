import os
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .models import user, company, company_followers, job_posts, job_applications, articles
from django.views.decorators.csrf import csrf_protect
from .utils import encrypt_id, get_user_by_encrypted_id, get_company_by_encrypted_id, get_company_follower_by_encrypted_id, get_job_post_by_encrypted_id, get_job_application_by_encrypted_id, get_article_by_encrypted_id
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
import traceback
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.core.validators import validate_email, URLValidator
import re


@csrf_protect
def welcome (request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_obj = authenticate(request, email=email, password=password)

        try: 
            user_obj = user.objects.get(email=email, role='0', status='1')
            if user_obj.check_password(password):
                request.session['user_id']=user_obj.id
                request.session['user_email']=user_obj.email
                request.session['user_name']=user_obj.full_name
                request.session['is_authenticated']=True

                messages.success(request, f'welcome back, {user_obj.full_name}!')

                return redirect('dashboard')
            else:
                messages.error(request, 'Access denied. Only a superuser can login here.')
       
        except Exception as e:
            messages.error(request, f'Login error: {str(e)}')
        except Exception as e:
            messages.error(request, f'Login error: {str(e)}')

    return render (request, 'welcome.html')
   

def super_admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            messages.error(request, 'please login first.')
            return redirect('welcome')
        
        user_id = request.session.get('user_id')
        try:
            user_id = user.objects.get(id=user_id, status = '1')
            if user_id.role != '0':
                messages.error(request, 'Access denied. super admin required.')
                return redirect('welcome')
        except user.DoesNotExist:
            messages.error(request, 'User not found') 
            return redirect('welcome')
        
        return view_func(request, *args, **kwargs)
    return wrapper



@super_admin_required
def dashboard(request):
    user_id = request.session.get('user_id')
    user_obj = user.objects.get(id=user_id)

    total_users= user.objects.exclude(status='5').count()
    total_companies= company.objects.exclude(status='5').count()
    total_follows= company_followers.objects.exclude(status='0').count()
    total_jobs= job_posts.objects.exclude(status='5').count()
    total_job_applications= job_applications.objects.exclude(status='5').count()
    total_articles= articles.objects.exclude(status='5').count()



    context = {
        'current_user': user_obj,
        'total_users': total_users,
        'total_companies': total_companies,
        'total_follows': total_follows,
        'total_jobs': total_jobs,
        'total_job_applications': total_job_applications,
        'total_articles': total_articles,


    }

    return render(request, 'dashboard.html', context)
    


@super_admin_required
def user_logout(request):
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('welcome')

@super_admin_required
def users(request):
    
    # users_list = user.objects.exclude(role='0').exclude(status=5).order_by('-created_at')

    # print(f"Users found: {users_list.count()}")
    # for usr in users_list:
    #     usr.md5_id = encrypt_id(usr.id)

    context = {
        # 'users': users_list,
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }

    return render(request, 'users.html', context)

@super_admin_required
def add_user(request):
    if request.method == 'POST':
        try:
            full_name = request.POST.get('full_name')
            username = request.POST.get('username')
            email = request.POST.get('email')
            phone_no = request.POST.get('phone_no')
            password = request.POST.get('password')
            role = request.POST.get('role')
            status = request.POST.get('status', '1')

            if user.objects.filter(email=email).exists():
                messages.error(request, 'A user with this email already exists.')
                return render(request, 'add_user.html')
            
            new_user = user(
                full_name=full_name,
                username=username if username else None,
                email=email,
                phone_no=phone_no,
                password=password,  
                role=role,
                status=status

            )
            new_user.save()

            messages.success(request, f'user {full_name} added successfully!')
            return redirect('users')
        except Exception as e:
            messages.error(request, f'Error adding member: {str(e)}')
            return render(request, 'add_user.html')
        
    context = {
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
        
    return render(request, 'add_user.html', context)

@super_admin_required
def edit_user(request, encrypted_id):
    user_obj=get_user_by_encrypted_id(encrypted_id)

    # user_obj=user.objects.get(id=encrypt_id)

    if request.method == 'POST':
        try: 
            full_name = request.POST.get('full_name')
            username = request.POST.get('username')
            email = request.POST.get('email')
            phone_no = request.POST.get('phone_no')
            role = request.POST.get('role')

            user_obj.full_name = full_name
            user_obj.username = username if username else None
            user_obj.email = email
            user_obj.phone_no = phone_no
            user_obj.role = role

            user_obj.updated_at = timezone.now()

            user_obj.save()
            messages.success(request, f'User {full_name} updated successfully!')

            return redirect('users')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')

        
    context = {
        'current_user': user.objects.get(id=request.session.get('user_id')),
        'user_obj': user_obj 

    }
        
    return render(request, 'edit_user.html', context)

@super_admin_required
def delete_user(request, encrypted_id):
    user_obj = get_user_by_encrypted_id(encrypted_id)

    try:
        # user_obj = user.objects.get(id=encrypt_id)
        user_obj.status = '5'
        user_obj.save()
        messages.success(request, f'User {user_obj.full_name} deleted successfully!')
        print(f"{user_obj.full_name} deleted!")
    except user.DoesNotExist:
        messages.error(request, 'User not found!')
    except Exception as e:
        messages.error(request, f'Error deleting user: {str(e)}')
        print(f'Error: {e}')
    
    return redirect('users')

@super_admin_required
def user_details(request, encrypted_id):
    user_obj = get_user_by_encrypted_id(encrypted_id)
    
    if not user_obj:
        messages.error(request, 'User not found!')
        return redirect('users')
    
    user_obj.md5_id = encrypt_id(user_obj.id)
    
    context = {
        'user_obj': user_obj,
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    
    return render(request, 'user_details.html', context)


@super_admin_required
def users_data(request):
    try:
        draw = int(request.GET.get('draw', 1))
        start=int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]','')

        queryset = user.objects.exclude(role='0').exclude(status='5')

        if search_value:
            queryset = queryset.filter(
                Q(full_name__icontains=search_value) |
                Q(email__icontains=search_value) |
                Q(username__icontains=search_value) |
                Q(phone_no__icontains=search_value)
            )



        records_total = int(user.objects.exclude(role='0').exclude(status='5').count())

        records_filtered = queryset.count()

        paginator = Paginator(queryset, length)
        page_number = start // length + 1
        page = paginator.get_page(page_number)
        data = []
        for usr in page:
            usr.md5_id = encrypt_id(usr.id)
            data.append({
                "full_name": usr.full_name,
                "username": usr.username,
                "email": usr.email,
                "phone_no": usr.phone_no or "",
                "actions": f"""
                    <div class='btn-group'>
                      <a href='/users/details/{usr.md5_id}/' class='btn btn-sm btn-primary'><i class='fas fa-eye'></i></a>
                      <a href='/users/edit/{usr.md5_id}/' class='btn btn-sm btn-warning'><i class='fas fa-edit'></i></a>
                      <a href='/users/delete/{usr.md5_id}/' class='btn btn-sm btn-danger' onclick="return confirm('Are you sure?')"><i class='fas fa-user-times'></i></a>
                    </div>

                """
            })

        return JsonResponse({
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data
    })
    except Exception as e:
        return JsonResponse({
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        })

@super_admin_required
def companies(request):
    company_list = company.objects.exclude(status='5').order_by('created_at')
    for comp in company_list:
        comp.md5_id = encrypt_id(comp.id)

    context = {
        'companies': company_list,
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    return render(request, 'companies.html', context)

@super_admin_required
def add_company(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone_no = request.POST.get('phone_no')
            address = request.POST.get('address')
            website = request.POST.get('website')

            errors = {}
            if not email:
                errors['email'] = 'Email is required.'
            else:
                try:
                    validate_email(email)
                except ValidationError:
                    errors['email'] = 'Enter a valid email address.'

                if company.objects.filter(email=email, status__in=['0', '1']).exists():
                    errors['email'] = 'A company with this email already exists.'

            if phone_no:

                phone_digits = re.sub(r'\D', '', phone_no)
                if len(phone_digits) < 10:
                    errors['phone'] = 'Please enter a valid phone number (at least 10 digits).'
                elif len(phone_no) > 20:
                    errors['phone'] = 'Phone number cannot exceed 20 characters.'

            if not name:
                errors['name'] = 'Company name is required.'
            elif len(name) > 255:
                errors['name'] = 'Company name cannot exceed 255 characters.'
            elif company.objects.filter(name=name, status__in=['0', '1']).exists():
                errors['name'] = 'A company with this name already exists.'

            if errors:
                for field, error_message in errors.items():
                    messages.error(request, error_message)
                context = {
                    'current_user': user.objects.get(id=request.session.get('user_id'))
                }
                return render(request, 'add_company.html', context)

            
            new_company = company(
                name=name,
                email=email,
                phone_no=phone_no,
                address=address,
                website=website
            )
            new_company.save()

            messages.success(request, f'Company {name} added successfully!')
            return redirect('companies')
            
        except Exception as e:
            messages.error(request, f'Error adding company: {str(e)}')
            return render(request, 'add_company.html')
    
    context = {
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    return render(request, 'add_company.html', context)

@super_admin_required
def edit_company(request, encrypted_id):
    company_obj = get_company_by_encrypted_id(encrypted_id)
    company_obj.md5_id=encrypt_id(company_obj.id)
    if request.method == 'POST':
        try: 
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone_no = request.POST.get('phone_no')
            address = request.POST.get('address')
            website = request.POST.get('website')
            status = request.POST.get('status')

            company_obj.name = name
            company_obj.email = email
            company_obj.phone_no = phone_no
            company_obj.address = address
            company_obj.website = website
            company_obj.status = status
            
            company_obj.updated_at = timezone.now()
            company_obj.save()
            messages.success(request, f'Company {name} updated successfully!')
            return redirect('companies')
            
        except Exception as e:
            messages.error(request, f'Error updating company: {str(e)}')
    
    context = {
        'current_user': user.objects.get(id=request.session.get('user_id')),
        'company_obj': company_obj
    }
    return render(request, 'edit_company.html', context)

@super_admin_required
def company_details(request, encrypted_id):
    company_obj = get_company_by_encrypted_id(encrypted_id)
    follower_count = company_followers.objects.filter(
        company=company_obj, 
        status='1'
    ).count()    
    company_obj.md5_id = encrypt_id(company_obj.id)
    company_obj.follower_count = follower_count

    context = {
        'company_obj': company_obj,
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    return render(request, 'company_details.html', context)

@super_admin_required
def delete_company(request, encrypted_id):
    company_obj = get_company_by_encrypted_id(encrypted_id)
    
    if not company_obj:
        messages.error(request, 'Company not found!')
        return redirect('companies')
    
    try:
        company_obj.status = '5'
        company_obj.save()
        messages.success(request, f'Company {company_obj.name} deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting company: {str(e)}')
    
    return redirect('companies')


@super_admin_required
def companies_data(request):
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        queryset = company.objects.exclude(status='5')

        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(email__icontains=search_value) |
                Q(phone_no__icontains=search_value) |
                Q(address__icontains=search_value) |
                Q(website__icontains=search_value)
            )

        records_total = company.objects.exclude(status='5').count()
        records_filtered = queryset.count()

        paginator = Paginator(queryset, length)
        page_number = start // length + 1
        page = paginator.get_page(page_number)
        
        data = []
        for comp in page:
            comp.md5_id = encrypt_id(comp.id)
            data.append({
                "name": comp.name or "",
                "email": comp.email or "",
                "phone_no": comp.phone_no or "",
                "website": comp.website or "",
                "address": comp.address or "",
                "actions": f"""
                    <div class='btn-group'>
                      <a href='/companies/details/{comp.md5_id}/' class='btn btn-sm btn-primary'><i class='fas fa-eye'></i></a>
                      <a href='/companies/edit/{comp.md5_id}/' class='btn btn-sm btn-warning'><i class='fas fa-edit'></i></a>
                      <a href='/companies/delete/{comp.md5_id}/' class='btn btn-sm btn-danger' onclick="return confirm('Are you sure you want to delete this company?')"><i class='fas fa-building'></i></a>
                    </div>
                """
            })

        response_data = {
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        })

@super_admin_required
def company_followers_list(request):
    context={
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    return render(request, 'company_followers_list.html', context)

@super_admin_required
def company_followers_data(request):
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # queryset = company_followers.objects.filter(status='1').select_related('user', 'company')
        queryset = company_followers.objects.exclude(status='0').select_related('user', 'company')


        if search_value:
            queryset = queryset.filter(
                Q(user__full_name__icontains=search_value) |
                Q(user__email__icontains=search_value) |
                Q(company__name__icontains=search_value) |
                Q(company__email__icontains=search_value)

            )
        records_total = company_followers.objects.exclude(status=5).count()
        records_filtered = queryset.count()

        queryset = queryset.order_by('-updated_at')

        paginator = Paginator(queryset, length)
        page_number = start // length + 1
        page = paginator.get_page(page_number)

        data = []
        for follower in page:
            user_md5 = encrypt_id(follower.user.id)
            company_md5 = encrypt_id(follower.company.id)
            # follower_md5 = 

            data.append({
                "user_name": f"<a href='/users/details/{user_md5}/'>{follower.user.full_name}</a>",
                "user_email": follower.user.email,
                "company_name": f"<a href='/companies/details/{company_md5}/'>{follower.company.name}</a>",
                "company_email": follower.company.email,
                "updated_at": follower.updated_at.strftime('%Y-%m-%d %H:%M:%S')if follower.updated_at else "",
                # "status": "<span class='badge badge-success'>Following</span>",
                "actions": f"""
                    <div class='btn-group'>
                        <a href='/company_followers/unfollow/{encrypt_id(follower.id)}/' 
                           class='btn btn-sm btn-danger' 
                           onclick="return confirm('Are you sure you want to unfollow?')">
                            <i class='fas fa-user-minus'></i>
                        </a>
                    </div>
                """
            })

        response_data = {
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        })


@super_admin_required
def get_companies_not_followed(request):
    user_id = request.GET.get('user_id')

    if not user_id:
        return JsonResponse({'companies': []})

    try: 
        user_obj = get_user_by_encrypted_id(user_id)
        if not user_obj:
            return JsonResponse({'companies':[]})
        
        all_companies = company.objects.exclude(status='5')

        followed_company_ids = company_followers.objects.filter(
            user=user_obj, 
            status='1'
        ).values_list('company_id', flat=True)

        available_companies = all_companies.exclude(id__in=followed_company_ids)
        
        companies_data = []
        for comp in available_companies:
            companies_data.append({
                'id': encrypt_id(comp.id),
                'name': comp.name,
                'email': comp.email
            })
        
        return JsonResponse({'companies': companies_data})

    except Exception as e:
        return JsonResponse({'companies': [], 'error': str(e)})


@super_admin_required
def add_company_follower(request):
    if request.method == 'POST':
        try:
            user_id = request.POST.get('user_id')
            company_id = request.POST.get('company_id')

            if not user_id or not company_id:
                messages.error(request, 'Both user and company are required.')
                return redirect('add_company_follower')
            user_obj = get_user_by_encrypted_id(user_id)
            company_obj = get_company_by_encrypted_id(company_id)

            if not user_obj or not company_obj:
                messages.error(request, 'Invalid user or company selected.')
                return redirect('add_company_follower')
            
            existing_follower = company_followers.objects.filter(
                user=user_obj,
                company=company_obj
            ).first()
            if existing_follower:
                if existing_follower.status == '1':
                    messages.warning(request, f'{user_obj.full_name} already follows {company_obj.name}' )
                    print(request, f'{user_obj.full_name} already follows {company_obj.name}')
                    return redirect('add_company_follower')
                else:
                    existing_follower.status = '1'
                    existing_follower.updated_at = timezone.now()
                    existing_follower.save()
                    messages.success(request, f'{user_obj.full_name} is now following {company_obj.name} again!')
            else:
                new_follower = company_followers(
                    user = user_obj,
                    company = company_obj,
                    status = '1'
                )
                new_follower.save()
                messages.success(request, f'Successfully added {user_obj.full_name} as follower of {company_obj.name}')
                print(f'Successfully added {user_obj.full_name} as follower of {company_obj.name}')

            return redirect ('company_followers_list')
        
        except Exception as e:
            messages.error(request, f'Error adding follower:{str(e)}')
            return redirect('add_company_follower')
        
    available_users = user.objects.exclude(status='5').exclude(role='0')
    for usr in available_users:
        usr.md5_id = encrypt_id(usr.id)
    
    context={
        'current_user': user.objects.get(id=request.session.get('user_id')),
        'users': available_users,  
        'companies':[]
    }
    return render(request, 'add_company_follower.html', context)


@super_admin_required
def unfollow_company(request, encrypted_id):
    try:
        follower = get_company_follower_by_encrypted_id(encrypted_id)
        
        if not follower:
            messages.error(request, 'Follower relationship not found!')
            return redirect('company_followers_list')
        
        user_name = follower.user.full_name
        company_name = follower.company.name
        
        follower.status = '0'
        follower.updated_at = timezone.now()
        follower.save()
        
        messages.warning(request, f'{user_name} has unfollowed {company_name}')
        
    except Exception as e:
        messages.error(request, f'Error unfollowing company: {str(e)}')
    
    return redirect('company_followers_list')

@super_admin_required
def job_posts_list(request):
    context = {
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    return render (request, 'job_posts_list.html', context)


@super_admin_required
def job_posts_data(request):
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')

        queryset = job_posts.objects.exclude(status='5').select_related('company')

        if search_value:
            queryset = queryset.filter(
                Q(job_title__icontains=search_value) |
                Q(requirements__icontains=search_value) |
                Q(salary_range__icontains=search_value) |
                Q(company__name__icontains=search_value) |
                Q(location__icontains=search_value) |
                Q(employment_type__icontains=search_value)
            )

        records_total = job_posts.objects.exclude(status='5').count()
        records_filtered = queryset.count()

        queryset = queryset.order_by('-created_at')

        paginator = Paginator(queryset, length)
        page_number = start // length + 1
        page = paginator.get_page(page_number)

        data = []
        for job in page:
            company_md5 = encrypt_id(job.company.id)
            job_md5 = encrypt_id(job.id)

            data.append({
                "job_title": job.job_title,
                "company_name": f"<a href='/companies/details/{company_md5}/'>{job.company.name}</a>",
                "location": job.location or "Not specified",
                "employment_type": job.get_employment_type_display(),
                "salary_range": job.salary_range or "Not specified",
                "requirements": job.requirements or "Not specified",
                "posted_on": job.created_at.strftime('%Y-%m-%d'),
                "actions": f"""
                    <div class='btn-group'>
                        <a href='/job_posts/details/{job_md5}/' class='btn btn-sm btn-primary' title="View Details">
                            <i class='fas fa-eye'></i>
                        </a>

                        <a href='/job_posts/edit/{job_md5}/' class='btn btn-sm btn-warning'>
                            <i class='fas fa-edit'></i>
                        </a>
                        <a href='/job_posts/delete/{job_md5}/' class='btn btn-sm btn-danger' 
                           onclick="return confirm('Are you sure you want to delete this job post?')">
                            <i class='fas fa-trash'></i>
                        </a>
                    </div>
                """
            })

        response_data = {
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        })





@super_admin_required
def add_job_post(request):
    if request.method == "POST":
        try:
            company_id = request.POST.get('company_id')
            job_title = request.POST.get('job_title')
            job_description = request.POST.get('job_description')
            requirements = request.POST.get('requirements')
            location = request.POST.get('location')
            salary_range = request.POST.get('salary_range')
            employment_type = request.POST.get('employment_type')

            if not company_id or not job_title:
                messages.error(request, 'Company and Job Title are required.')
                return redirect('add_job_post')
            
            company_obj = get_company_by_encrypted_id(company_id)
            
            new_job_post = job_posts(
                company=company_obj,
                job_title=job_title,
                job_description=job_description,
                requirements=requirements,
                location=location,
                salary_range=salary_range,
                employment_type=employment_type
            )
            new_job_post.save()
            messages.success(request, f'Job post "{job_title}" added successfully!')
            return redirect('job_posts_list')

        except Exception as e:
            print(request, f'Error adding job post: {str(e)}')
            messages.error(request, f'Error adding job post: {str(e)}')
            return redirect('add_job_post')
        
    available_companies = company.objects.exclude(status='5')
    for comp in available_companies:
        comp.md5_id = encrypt_id(comp.id)

    context = {
        'current_user': user.objects.get(id=request.session.get('user_id')),
        'companies': available_companies,
        'employment_types': job_posts.EMPLOYMENT_TYPE_CHOICES
    }
    return render(request, 'add_job_post.html', context)


@super_admin_required
def job_post_details(request, encrypted_id):
    job_post = get_job_post_by_encrypted_id(encrypted_id)
    
    if not job_post:
        messages.error(request, 'Job post not found!')
        return redirect('job_posts_list')
    
    job_post.md5_id = encrypt_id(job_post.id)
    company_md5 = encrypt_id(job_post.company.id)
    
    context = {
        'job_post': job_post,
        'company_md5': company_md5,
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    
    return render(request, 'job_post_details.html', context)


@super_admin_required
def edit_job_post(request, encrypted_id):
    job_post = get_job_post_by_encrypted_id(encrypted_id)
    
    if not job_post:
        messages.error(request, 'Job post not found!')
        return redirect('job_posts_list')
    
    if request.method == "POST":
        try:
            company_id = request.POST.get('company_id')
            job_title = request.POST.get('job_title')
            job_description = request.POST.get('job_description')
            requirements = request.POST.get('requirements')
            location = request.POST.get('location')
            salary_range = request.POST.get('salary_range')
            employment_type = request.POST.get('employment_type')

            company_obj = get_company_by_encrypted_id(company_id)

            job_post.company = company_obj
            job_post.job_title = job_title
            job_post.job_description = job_description
            job_post.requirements = requirements
            job_post.location = location
            job_post.salary_range = salary_range
            job_post.employment_type = employment_type
            job_post.updated_at=timezone.now()
            job_post.save()

            messages.success(request, f'Job post "{job_title}" updated successfully!')
            return redirect('job_posts_list')

        except Exception as e:
            print(f'Error updating job post: {str(e)}')
            messages.error(request, f'Error updating job post: {str(e)}')
            return redirect('edit_job_post', encrypted_id=encrypted_id)

    available_companies = company.objects.exclude(status='5')
    for comp in available_companies:
        comp.md5_id = encrypt_id(comp.id)

    context = {
        'current_user': user.objects.get(id=request.session.get('user_id')),
        'job_post': job_post,
        'companies': available_companies,
        'employment_types': job_posts.EMPLOYMENT_TYPE_CHOICES
    }
    return render(request, 'edit_job_post.html', context)

@super_admin_required 
def delete_job_post(request, encrypted_id):
    job_post = get_job_post_by_encrypted_id(encrypted_id)

    try:
        job_title = job_post.job_title
        job_post.status ='5'
        job_post.save()

        messages.success(request, f'Job post "{job_title}" deleted successfully!')
        print(f'Job post "{job_title}" deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting job post: {str(e)}')
        print(f'Error deleting job post: {str(e)}')
    
    return redirect('job_posts_list')

@super_admin_required
def job_applications_list(request):
    context={
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    return render (request, 'job_applications_list.html', context)

@super_admin_required
def job_applications_data(request):
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        job_filter = request.GET.get('job_filter', '')
        status_filter = request.GET.get('status_filter', '')
        
        queryset = job_applications.objects.exclude(status='5').select_related('job', 'user', 'job__company')

        if search_value:
            queryset = queryset.filter(
                Q(user__full_name__icontains=search_value) |
                Q(user__email__icontains=search_value) |
                Q(job__job_title__icontains=search_value) |
                Q(job__company__name__icontains=search_value) |
                Q(about__icontains=search_value)
            )
        if job_filter:
            job_obj = get_job_post_by_encrypted_id(job_filter)
            if job_obj:
                queryset = queryset.filter(job=job_obj)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        request_total = job_applications.objects.exclude(status='5').count()
        record_filtered = queryset.count()

        queryset = queryset.order_by('-applied_at')

        paginator = Paginator(queryset, length)
        page_number = start // length + 1
        page = paginator.get_page(page_number)

        data = []
        for application in page:
            user_md5 = encrypt_id(application.user.id)
            job_md5 = encrypt_id(application.job.id)
            application_md5 = encrypt_id(application.id)

            status_badges = {
                '0': '<span class="badge badge-warning">Applied</span>',
                '1': '<span class="badge badge-success">Approved</span>',
                '2': '<span class="badge badge-danger">Rejected</span>',
                '3': '<span class="badge badge-secondary">Withdrawn</span>',
            }
            resume_link = ''
            if application.resume:
                resume_link = f'<a href="{application.resume.url}" class="btn btn-sm btn-outline-primary" target="_blank" title="Download Resume"><i class="fas fa-download"></i></a>'
            else:
                resume_link = '<span class="text-muted">No resume</span>'

            data.append({
                "applicant_name": f"<a href='/users/details/{user_md5}/'>{application.user.full_name}</a>",
                "applicant_email": application.user.email,
                "job_title": f"<a href='/job-posts/details/{job_md5}/'>{application.job.job_title}</a>",
                "company": application.job.company.name,
                "applied_at": application.applied_at.strftime('%Y-%m-%d %H:%M'),
                "status": status_badges.get(application.status, '<span class="badge badge-secondary">Unknown</span>'),
                "resume": resume_link,
                "actions": f"""
                    <div class='btn-group'>
                        <a href='/job_application/details/{application_md5}/' class='btn btn-sm btn-primary' title="View Details">
                            <i class='fas fa-eye'></i>
                        </a>

                        <a href='/job_application/edit/{application_md5}/' class='btn btn-sm btn-warning'>
                            <i class='fas fa-edit'></i>
                        </a>
                        <a href='/job_application/delete/{application_md5}/' class='btn btn-sm btn-danger' 
                           onclick="return confirm('Are you sure you want to delete this application?')">
                            <i class='fas fa-trash'></i>
                        </a>
                    </div>
                """
            })

        response_data = {
            "draw": draw,
            "recordsTotal": request_total,
            "recordsFiltered": record_filtered,
            "data": data
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        })

@super_admin_required
def add_job_application(request):
    if request.method == 'POST':
        try: 
            job_id = request.POST.get('job_id')
            user_id = request.POST.get('user_id')
            about = request.POST.get('about', '')
            resume = request.FILES.get('resume')

            if not job_id or not user_id:
                messages.error(request, 'Job and User are required.')
                return redirect('add_job_application')

            if not resume:
                messages.error(request, 'Resume file is required.')
                return redirect('add_job_application')
            
            job_obj = get_job_post_by_encrypted_id(job_id)
            user_obj = get_user_by_encrypted_id(user_id)

            if not job_obj or not user_obj:
                messages.error(request, 'Invalid job or user selected.')
                return redirect('add_job_application')

            existing_application = job_applications.objects.filter(
                job=job_obj, 
                user=user_obj
            ).exclude(status='5').first()

            if existing_application:
                messages.warning(request, f'{user_obj.full_name} has already applied for this job!')
                return redirect('add_job_application')

            if resume:
                if resume.size > 5 * 1024 * 1024:
                    messages.error(request, 'Resume file size must be less than 5MB.')

                    return redirect ('add_job_application')
                
                if not resume.name.lower().endswith('.pdf'):
                    messages.error(request, 'Only PDF files are allowed for resumes.')
                    return redirect('add_job_application')
                
                new_application= job_applications(
                    job=job_obj,
                    user=user_obj,
                    about=about,
                    resume=resume,
                    status='0'  
                )
                new_application.save()

            messages.success(request, f'Job application for {user_obj.full_name} added successfully!')
            return redirect('job_applications_list')

        except Exception as e:
            print(f'Error adding job application: {str(e)}')
            messages.error(request, f'Error adding job application: {str(e)}')
            return redirect('add_job_application')
    
    available_jobs = job_posts.objects.filter(status='1')
    available_users = user.objects.exclude(status='5').exclude(role='0')

    for job in available_jobs:
        job.md5_id = encrypt_id(job.id)
    for usr in available_users:
        usr.md5_id = encrypt_id(usr.id)

    context = {
        'current_user': user.objects.get(id=request.session.get('user_id')),
        'jobs': available_jobs,
        'users': available_users
    }
    return render(request, 'add_job_application.html', context)

@super_admin_required
def get_users_not_applied(request):
    job_id = request.GET.get('job_id')
    
    if not job_id:
        return JsonResponse({'users': []})
    
    try:
        job_obj = get_job_post_by_encrypted_id(job_id)
        if not job_obj:
            return JsonResponse({'users': []})

        all_users = user.objects.exclude(status='5').exclude(role='0')
        applied_user_ids = job_applications.objects.filter(
            job=job_obj
        ).exclude(status='5').values_list('user_id', flat=True)

        available_users = all_users.exclude(id__in=applied_user_ids)

        users_data = []
        for usr in available_users:
            users_data.append({
                'id': encrypt_id(usr.id),
                'name': usr.full_name,
                'email': usr.email
            })
        
        return JsonResponse({'users': users_data})
        
    except Exception as e:
        return JsonResponse({'users': [], 'error': str(e)})

@super_admin_required
def job_application_details(request, encrypted_id):
    application = get_job_application_by_encrypted_id(encrypted_id)

    application.md5_id = encrypt_id(application.id)
    user_md5 = encrypt_id(application.user.id)
    job_md5 = encrypt_id(application.job.id)
    company_md5 = encrypt_id(application.job.company.id)
    
    context = {
        'application': application,
        'user_md5': user_md5,
        'job_md5': job_md5,
        'company_md5': company_md5,
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    return render(request, 'job_application_details.html', context)

@super_admin_required
def edit_job_application(request, encrypted_id):
    application = get_job_application_by_encrypted_id(encrypted_id)

    if request.method == "POST":
        try:
            about = request.POST.get('about', '')
            status = request.POST.get('status')
            resume = request.FILES.get('resume')
            application.about = about
            application.status = status
            if resume:
                if resume.size > 5 * 1024 * 1024:
                    messages.error(request, 'Resume file size must be less than 5MB.')
                    return redirect('edit_job_application', encrypted_id=encrypted_id)
                if not resume.name.lower().endswith('.pdf'):
                    messages.error(request, 'Only PDF files are allowed for resumes.')
                    return redirect('edit_job_application', encrypted_id=encrypted_id)

                if application.resume:
                    try:
                        if os.path.isfile(application.resume.path):
                            os.remove(application.resume.path)
                    except Exception as e:
                        print(f"Error deleting old resume: {e}")

                application.resume = resume
            application.updated_at = timezone.now()
            application.save()

            messages.success(request, f'Job application for {application.user.full_name} updated successfully!')
            return redirect('job_applications_list')

        except Exception as e:
            print(f'Error updating job application: {str(e)}')
            messages.error(request, f'Error updating job application: {str(e)}')
            return redirect('edit_job_application', encrypted_id=encrypted_id)
    context = {
        'current_user': user.objects.get(id=request.session.get('user_id')),
        'application': application,
        'status_choices': [
            ('0', 'Applied'),
            ('1', 'Approved'), 
            ('2', 'Rejected'),
            ('3', 'Withdrawn')
        ]
    }
    return render(request, 'edit_job_application.html', context)

@super_admin_required
def delete_job_application(request, encrypted_id):
    application = get_job_application_by_encrypted_id(encrypted_id)

    try:
        user_name = application.user.full_name
        job_title = application.job.job_title
        application.status ='5'
        application.save()


        messages.success(request, f'application for "{job_title}" deleted successfully!')
        print(f'Application for "{job_title}" deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting job application: {str(e)}')
        print(f'Error deleting job application: {str(e)}')
    
    return redirect('job_applicationsS_list')

@super_admin_required
def articles_list(request):
    context = {
        'current_user': user.objects.get(id=request.session.get('user_id'))
    }
    return render(request, 'articles_list.html', context)

@super_admin_required
def articles_data(request):
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        category_filter = request.GET.get('category_filter', '')
        company_filter = request.GET.get('company_filter', '')
        
        queryset = articles.objects.exclude(status='5').select_related('company')


        if search_value:
            queryset = queryset.filter(
                Q(title__icontains=search_value) |
                Q(content__icontains=search_value) |
                Q(company__name__icontains=search_value) 
            )

        if category_filter:
            queryset = queryset.filter(category=category_filter)

        if company_filter:
            company_obj = get_company_by_encrypted_id(company_filter)
            if company_obj:
                queryset = queryset.filter(company=company_obj)

        records_total = articles.objects.exclude(status='5').count()
        records_filtered = queryset.count()

        queryset = queryset.order_by('-published_at')

        paginator = Paginator(queryset, length)
        page_number = start // length + 1
        page = paginator.get_page(page_number)

        data = []
        for article in page:
            company_md5 = encrypt_id(article.company.id)
            article_md5 = encrypt_id(article.id)

            category_badge = f'<span class="badge badge-info">{article.get_category_display()}</span>'
            image_thumbnail = ''
            if article.image:
                image_thumbnail = f'<img src="{article.image.url}" width="50" height="50" class="rounded" alt="Article Image" style="object-fit: cover;">'
            else:
                image_thumbnail = '<span class="text-muted">No Image</span>'

        data.append({
                "title": article.title,
                "company": f"<a href='/companies/details/{company_md5}/'>{article.company.name}</a>",
                "category": category_badge,
                "image": image_thumbnail,
                "published_at": article.published_at.strftime('%Y-%m-%d') if article.published_at else "Not published",
                "actions": f"""
                    <div class='btn-group'>
                        <a href='/articles/details/{article_md5}/' class='btn btn-sm btn-primary' title="View Details">
                            <i class='fas fa-eye'></i>
                        </a>
                        <a href='/articles/edit/{article_md5}/' class='btn btn-sm btn-warning' title="Edit">
                            <i class='fas fa-edit'></i>
                        </a>
                        <a href='/articles/delete/{article_md5}/' class='btn btn-sm btn-danger' 
                           onclick="return confirm('Are you sure you want to delete this article?')" title="Delete">
                            <i class='fas fa-trash'></i>
                        </a>
                    </div>
                """
            })
        response_data = {
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data
        }
        
        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        })

@super_admin_required
def add_article(request):
    if request.method == "POST":
        try:
            company_id = request.POST.get('company_id')
            title = request.POST.get('title')
            content = request.POST.get('content')
            category = request.POST.get('category')
            image = request.FILES.get('image')  
            
            
            company_obj = get_company_by_encrypted_id(company_id)
            if not company_obj:
                messages.error(request, 'Invalid company selected.')
                return redirect('add_article')
            if image:
                if image.size > 2 * 1024 * 1024:
                    messages.error(request, 'Image size must be less than 2MB.')
                    return redirect('add_article')
                allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
                if image.content_type not in allowed_types:
                    messages.error(request, 'Only JPEG, PNG, GIF, and WebP images are allowed.')
                    return redirect('add_article')


            new_article = articles(
                company=company_obj,
                title=title,
                content=content,
                category=category,
                image=image
            )
            new_article.save()

            messages.success(request, f'Article "{title}" added successfully!')
            return redirect('articles_list')
        except Exception as e:
            print(f'Error adding article: {str(e)}')
            messages.error(request, f'Error adding article: {str(e)}')
            return redirect('add_article')
    available_companies = company.objects.exclude(status='5')
    for comp in available_companies:
        comp.md5_id = encrypt_id(comp.id)

    context = {
        'current_user': user.objects.get(id=request.session.get('user_id')),
        'companies': available_companies,
        'categories': articles.CATEGORY_CHOICES
    }
    return render(request, 'add_article.html', context)

@super_admin_required
def edit_article(request, encrypted_id):
    article = get_article_by_encrypted_id(encrypted_id)

    if request.method == "POST":
        try:
            company_id = request.POST.get('company_id')
            category = request.POST.get('category')
            title = request.POST.get('title')
            content = request.POST.get('content')
            image = request.FILES.get('image')
            remove_image = request.POST.get('remove_image')  

            if not company_id or not title or not content:
                messages.error(request, 'Company, Title, and Content are required.')
                return redirect('edit_article', encrypted_id=encrypted_id)

            company_obj = get_company_by_encrypted_id(company_id)
            if not company_obj:
                messages.error(request, 'Invalid company selected.')
                return redirect('edit_article', encrypted_id=encrypted_id)

            article.company = company_obj
            article.title = title
            article.content = content
            article.category = category
            

            if remove_image and article.image:
                article.image.delete(save=False)
                article.image = None

            if image:
                if image.size > 2 * 1024 * 1024:
                    messages.error(request, 'Image size must be less than 2MB.')
                    return redirect('edit_article', encrypted_id=encrypted_id)
                
                allowed_types = ['image/jpeg', 'image/png']

                if image.content_type not in allowed_types:
                    messages.error(request, 'Only JPEG, PNG images are allowed.')
                    return redirect('edit_article', encrypted_id=encrypted_id)
                
                if article.image:
                    article.image.delete(save=False)
                
                article.image = image
                
            article.updated_at=timezone.now()
            article.save()

            messages.success(request, f'Article "{title}" updated successfully!')
            return redirect('articles_list')

        except Exception as e:
            print(f'Error updating article: {str(e)}')
            messages.error(request, f'Error updating article: {str(e)}')
            return redirect('edit_article', encrypted_id=encrypted_id)
        
    available_companies = company.objects.exclude(status='5')
    for comp in available_companies:
        comp.md5_id = encrypt_id(comp.id)

    context = {
        'current_user': user.objects.get(id=request.session.get('user_id')),
        'article': article,
        'companies': available_companies,
        'categories': articles.CATEGORY_CHOICES
    }
    return render(request, 'edit_article.html', context)

@super_admin_required
def delete_article(request, encrypted_id):
    article = get_article_by_encrypted_id(encrypted_id)

    try:
        title = article.title
        article.status = '5'
        article.save()
        messages.success(request, f'Article "{title}" deleted successfully!')
        
    except Exception as e:
        messages.error(request, f'Error deleting article: {str(e)}')
    
    return redirect('articles_list')

# @super_admin_required
# def article_details(request, encrypted_id):
#     article_md5 = get_article_by_encrypted_id(encrypted_id)

#     company_md5 = encrypt_id(article_md5.company.id)
#     # article_md5 = encrypt_id(article.id) 

#     company_md5 = get_company_by_encrypted_id(encrypted_id)

#     context = {
#         # 'article_md5': article,
#         'article_md5': article_md5,
#         'company_md5': company_md5,
#         'current_user': user.objects.get(id=request.session.get('user_id'))
#     }
#     return render(request, 'article_details.html', context)

@super_admin_required
def article_details(request, encrypted_id):
    try:
        article = get_article_by_encrypted_id(encrypted_id)

        company_md5 = encrypt_id(article.company.id)
        
        article_md5 =  encrypted_id
        
        context = {
            'article': article,  
            'article_md5': article_md5,  
            'company_md5': company_md5,  
            'current_user': user.objects.get(id=request.session.get('user_id'))
        }
        return render(request, 'article_details.html', context)
        
    except Exception as e:
        print(f"Error in article_details: {str(e)}")
        messages.error(request, f"Error loading article: {str(e)}")
        return redirect('articles_list')




