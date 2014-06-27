from difflib import context_diff

__author__ = 'Manuel'
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from DjangoTest.models import Category, Page

def get_url_from_category_name(catName):
    return catName.replace(' ', '_')

def get_category_name_from_url(url):
    return url.replace('_', ' ')

def index(request):
    context = RequestContext(request)
    category_list = Category.objects.order_by('-likes')[:5]
    pages_list = Page.objects.order_by('-views')[:5]
    context_dict = {'categories': category_list,
                    'pages' : pages_list}
    for category in category_list:
        category.url = get_url_from_category_name(category.name)
    return render_to_response('rango/index.html', context_dict, context)
def about(request):
    return HttpResponse("Rango Says: Here is the about page <a href='/DjangoTest'>Go to index</a>")
def category(request, category_name_url):
    context = RequestContext(request)
    category_name = get_category_name_from_url(category_name_url)

    context_dict = { 'category_name' : category_name }

    try:
        category = Category.objects.get(name=category_name)
        pages = Page.objects.filter(category=category)
        context_dict['pages'] = pages
        context_dict['category'] = category
    except Category.DoesNotExist:
        pass
    return render_to_response('rango/category.html', context_dict, context)