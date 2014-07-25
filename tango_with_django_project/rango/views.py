from django.template import RequestContext
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from rango.models import Category, Page, UserProfile
from rango.forms import CategoryForm, PageForm

from rango.forms import UserForm, UserProfileForm

from rango.bing_search import run_query

from datetime import datetime

def index(request):
    context = RequestContext(request)
    context_dict = {}
    
    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list
    
    page_list = Page.objects.order_by('-views')[:5]
    context_dict['pages'] = page_list

    if request.session.get('last_visit'):
        last_visit_time = request.session.get('last_visit')
        visits = request.session.get('visits', 0)

        if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).days > 0:
            request.session['visits'] = visits + 1
            request.session['last_visit'] = str(datetime.now())

    else:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = 1
        
    return render_to_response('rango/index.html', context_dict, context)

    

def about(request):
    context = RequestContext(request)
    context_dict = {}

    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list
    
    if request.session.get('visits'):
        count = request.session.get('visits')
    else:
        count = 0

    context_dict['visits'] = count
    
    return render_to_response('rango/about.html', context_dict, context)

def category(request, category_name_url):
    context = RequestContext(request)

    category_name = category_name_url.replace('_', ' ')

    context_dict = {'category_name' : category_name,
                    'category_name_url': category_name_url}

    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list
    
    try:
        category = Category.objects.get(name=category_name)

        pages = Page.objects.filter(category=category)

        context_dict['pages'] = sorted(pages, key=lambda x: x.views, reverse=True)

        context_dict['category'] = category
    except Category.DoesNotExist:
        pass

    result_list = []
    
    if request.method == 'POST':
        query = request.POST['query'].strip()
        
        if query:
            result_list = run_query(query)
            context_dict['result_list'] = result_list

    
    return render_to_response('rango/category.html', context_dict, context)


@login_required
def like_category(request):
    context = RequestContext(request)
    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['category_id']

    likes = 0
    if cat_id:
        category = Category.objects.get(id=int(cat_id))
        if category:
            likes = category.likes + 1
            category.likes =  likes
            category.save()

    return HttpResponse(likes)    

def suggest_category(request):
    context = RequestContext(request)
    cat_list = []
    starts_with = ''
    if request.method == 'GET':
        starts_with = request.GET['suggestion']

    cat_list = get_category_list(8, starts_with)

    return render_to_response('rango/category_list.html', {'cat_list': cat_list }, context)
    


def search(request):
    context = RequestContext(request)
    result_list = []

    cat_list = get_category_list()
    
    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            result_list = run_query(query)

    return render_to_response('rango/search.html', {'result_list': result_list, 'cat_list' : cat_list},context)

def track_url(request):
    context = RequestContext(request)

    url = "/rango/"
    page_id = None
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except:
                pass
    
    return redirect(url)

def register(request):
    context = RequestContext(request)
    
    context_dict = {}
    cat_list = get_category_list()

    context_dict['cat_list'] = cat_list
    
    registered = False

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()
            registered = True

        else:
            print user_form.errors, profile_form.errors

    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    context_dict['registered'] = registered
    context_dict['user_form'] = user_form
    context_dict['profile_form'] = profile_form
     
    return render_to_response('rango/register.html',    context_dict, context)



def user_login(request):
    context = RequestContext(request)

    cat_list = get_category_list()
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                return HttpResponse("Your Rango account is disabled.")
        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")
    else:
        return render_to_response('rango/login.html', {'cat_list' : cat_list}, context)


def user_logout(request):
    logout(request)

    return HttpResponseRedirect('/rango/')
    
@login_required
def add_page(request, category_name_url):
    context = RequestContext(request)

    category_name = decode_url(category_name_url)
    cat_list = get_category_list()

    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            page = form.save(commit=False)

            # Automatically add to proper category unless...
            # Category does not exist, in which case, ask the user to add it.
            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:
                return render_to_response('rango/add_category.html', {}, context)

            page.views = 0

            page.save()
            # After done sending form, send user to category page
            # To show that their changes went through
            return category(request, category_name_url)

        else:
            # Invalid form needs to tell user what about it is invalid
            print form.errors
    else:
        form = PageForm()

    return render_to_response('rango/add_page.html',
                              {'category_name_url': category_name_url,
                               'category_name' : category_name,
                              'form': form,
                              'cat_list' : cat_list},
                              context)

@login_required
def add_category(request):
    context = RequestContext(request)

    cat_list = get_category_list()

    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            print form.errors
    else:
        form = CategoryForm()

    return render_to_response('rango/add_category.html', {'form' : form, 'cat_list' : cat_list}, context)

@login_required
def profile(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    context_dict = {'cat_list': cat_list}

    u = User.objects.get(username=request.user)
    try:
        up = UserProfile.objects.get(user=u)
    except:
        up = None

    context_dict['user'] = u
    context_dict['user_profile'] = up
    if request.session.get('last_visit'):
        last_visit = request.session['last_visit']

    context_dict['last_visit'] =  datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")

    return render_to_response('rango/profile.html',
                              context_dict, context)
    

@login_required
def restricted(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    
    return render_to_response('rango/restricted.html', {'cat_list':cat_list}, context)

def decode_url(url):
    return url.replace('_', ' ')

def encode_url(url):
    return url.replace(' ', '_')
    
    
def get_category_list():
    category_list = Category.objects.all()

    for category in category_list:
        category.url = encode_url(category.name)

    return category_list
    
