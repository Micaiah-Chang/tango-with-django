from django.http import HttpResponse
from django.conf.urls import url
from django.template import RequestContext
from django.shortcuts import render_to_response

from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm

def add_page(request, category_name_url):
    context = RequestContext(request)

    category_name = decode_url(category_name_url)
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
                              'form': form},
                              context)


def add_category(request):
    context = RequestContext(request)

    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            print form.errors
    else:
        form = CategoryForm()

    return render_to_response('rango/add_category.html', {'form' : form}, context)


def index(request):
    context = RequestContext(request)

    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]
    
    context_dict = {'categories' : category_list,
                    'pages' : page_list}

    for category in category_list:
        category.url = category.name.replace(' ','_')
    
    return render_to_response('rango/index.html', context_dict, context)

def about(request):
    context = RequestContext(request)
    context_dict = {}
    
    return render_to_response('rango/about.html', context_dict, context)

def category(request, category_name_url):
    context = RequestContext(request)

    category_name = category_name_url.replace('_', ' ')

    context_dict = {'category_name' : category_name,
                    'category_name_url': category_name_url}

    try:
        category = Category.objects.get(name=category_name)

        pages = Page.objects.filter(category=category)

        context_dict['pages'] = pages

        context_dict['category'] = category
    except Category.DoesNotExist:
        pass

    return render_to_response('rango/category.html', context_dict, context)

def decode_url(url):
    return url.replace('_', ' ')

def encode_url(url):
    return ulr.replace(' ', '_')
    
    
