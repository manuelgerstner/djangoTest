from difflib import context_diff

__author__ = 'Manuel'
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from DjangoTest.models import Category, Page, UserProfile, User
from DjangoTest.forms import CategoryForm, PageForm, UserProfileForm, UserForm
from DjangoTest.bing_search import run_query
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime


def get_url_from_category_name(catName):
    return catName.replace(' ', '_')


def get_category_name_from_url(url):
    return url.replace('_', ' ')


def get_category_list():
     category_list = Category.objects.order_by('-likes')[:5]
     for category in category_list:
        category.url = get_url_from_category_name(category.name)
     return category_list


def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
        cat_list = Category.objects.filter(name__istartswith=starts_with)
    else:
        cat_list = Category.objects.all()

    if max_results > 0:
        if len(cat_list) > max_results:
            cat_list = cat_list[:max_results]

    for cat in cat_list:
        cat.url = get_url_from_category_name(cat.name)
    return cat_list


def index(request):
    context = RequestContext(request)
    request.session.set_test_cookie()

    pages_list = Page.objects.order_by('-views')[:5]

    context_dict = {'categories': get_category_list(),
                    'pages' : pages_list}

     # Obtain our Response object early so we can add cookie information.
    if request.session.get('last_visit'):
        # The session has a value for the last visit
        last_visit_time = request.session.get('last_visit')
        visits = request.session.get('visits', 0)

        if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).seconds > 5:
            request.session['visits'] = visits + 1
            request.session['last_visit'] = str(datetime.now())
    else:
        # The get returns None, and the session does not have a value for the last visit.
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = 1

    # Return response back to the user
    return render_to_response('rango/index.html', context_dict, context)


def about(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    if request.session.get('visits'):
        count = request.session.get('visits')
    else:
        count = 0


    context_dict = {'categories': cat_list,
                    'views': count }

    return render_to_response('rango/about.html', context_dict, context)


def category(request, category_name_url):
    context = RequestContext(request)
    category_name = get_category_name_from_url(category_name_url)

    result_list = ''
    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

    context_dict = { 'category_name': category_name,
                     'category_name_url': category_name_url,
                     'categories': get_category_list(),
                     'result_list': result_list}

    try:
        category = Category.objects.get(name=category_name)
        pages = Page.objects.filter(category=category)
        context_dict['pages'] = pages
        context_dict['category'] = category
    except Category.DoesNotExist:
        pass
    return render_to_response('rango/category.html', context_dict, context)


def add_category(request):
    # Get the context from the request.
    context = RequestContext(request)

    cat_list = get_category_list()

    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            # Save the new category to the database.
            form.save(commit=True)

            # Now call the index() view.
            # The user will be shown the homepage.
            return index(request)
        else:
            # The supplied form contained errors - just print them to the terminal.
            print form.errors
    else:
        # If the request was not a POST, display the form to enter details.
        form = CategoryForm()

    # Bad form (or form details), no form supplied...
    # Render the form with error messages (if any).
    return render_to_response('rango/add_category.html', {'categories': cat_list, 'form': form}, context)


def add_page(request, category_name_url):
    # Get the context from the request.
    context = RequestContext(request)

    cat_list = get_category_list()

    category_name = get_category_name_from_url(category_name_url)

    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            # This time we cannot commit straight away.
            # Not all fields are automatically populated!
            page = form.save(commit=False)

            # Retrieve the associated Category object so we can add it.
            # Wrap the code in a try block - check if the category actually exists!
            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:
                # If we get here, the category does not exist.
                # Go back and render the add category form as a way of saying the category does not exist.
                return render_to_response('rango/add_category.html', {'categories': cat_list}, context)

            # Also, create a default value for the number of views.
            page.views = 0

            # With this, we can then save our new model instance.
            page.save()

            # Now that the page is saved, display the category instead.
            return category(request, category_name_url)
        else:
            print form.errors
    else:
        form = PageForm()

    return render_to_response( 'rango/add_page.html',
            {'category_name_url': category_name_url,
             'category_name': category_name,'categories': cat_list, 'form': form}, context)


def register(request):
    # Like before, get the request's context.
    context = RequestContext(request)

    if request.session.test_cookie_worked():
        print ">>>> TEST COOKIE WORKED!"
        request.session.delete_test_cookie()

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance.
            profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors, profile_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Render the template depending on the context.
    return render_to_response(
            'rango/register.html',
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered},
            context)


def user_login(request):
    # Like before, obtain the context for the user's request.
    context = RequestContext(request)

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/DjangoTest/')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your Rango account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render_to_response('rango/login.html', {}, context)


@login_required
def restricted(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    context_dict = {'categories': cat_list}
    return render_to_response('rango/restricted.html', context_dict, context)

@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/DjangoTest/')


def search(request):
    context = RequestContext(request)
    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

    return render_to_response('rango/search.html', {'result_list': result_list}, context)


@login_required
def profile(request):
    context = RequestContext(request)

    cat_list = get_category_list()
    context_dict = {'categories': cat_list}

    usr = User.objects.get(username=request.user)

    try:
        user_profile = UserProfile.objects.get(user=usr)
    except:
        user_profile = None

    context_dict['user'] = usr
    context_dict['userprofile'] = user_profile

    return render_to_response('rango/profile.html', context_dict, context)


def track_url(request):

    if request.method == 'GET':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        page_id = request.GET.get('page_id')
        if page_id:
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
            except:
                pass
            if page:
                return HttpResponseRedirect(page.url)
            else:
                return HttpResponseRedirect('/DjangoTest/')
        else:
            return HttpResponseRedirect('/DjangoTest/')
    else:
        return HttpResponseRedirect('/DjangoTest/')


@login_required
def like_category(request):
    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['category_id']

    likes = 0
    if cat_id:
        category = Category.objects.get(id=int(cat_id))
        if category:
            likes = category.likes + 1
            category.likes = likes
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