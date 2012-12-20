from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.comments.views.comments import CommentPostBadRequest
from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.db import models
from django.template.context import RequestContext
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponseNotAllowed
from django.core import urlresolvers
from django.conf import settings
from django.contrib.comments.signals import comment_was_posted
from django.contrib.comments.models import Comment

from model_comments.forms import CommentForm
from model_comments.utils import get_form_class_for_object
from twigcorp.utils import Url
from django.contrib.auth.decorators import login_required


@csrf_protect
@require_POST
def post_comment(request, using = None):
    """
    This was copied mostly from django.contrib.comments.views.comments.post_comment()
    The behaviour was changed so it validates within a Form.
    ---
    Post a comment.

    HTTP POST is required. If ``POST['submit'] == "preview"`` or if there are
    errors a preview template, ``comments/preview.html``, will be rendered.
    """
    # Fill out some initial data fields from an authenticated user, if present
    data = request.POST.copy()
    
    if request.user.is_authenticated():
        if not data.get('name', ''):
            data["name"] = request.user.get_full_name() or request.user.username
        if not data.get('email', ''):
            data["email"] = request.user.email


    # Look up the object we're trying to comment about
    ctype = data.get("content_type")
    object_pk = data.get("object_pk")
    if ctype is None or object_pk is None:
        return CommentPostBadRequest("Missing content_type or object_pk field.")
    try:
        model = models.get_model(*ctype.split(".", 1))
        target = model._default_manager.using(using).get(pk=object_pk)
    except TypeError:
        return CommentPostBadRequest("Invalid content_type value: %r" % escape(ctype))
    except AttributeError:
        return CommentPostBadRequest("The given content-type %r does not resolve to a valid model." % escape(ctype))
    except ObjectDoesNotExist:
        return CommentPostBadRequest("No object matching content-type %r and object PK %r exists." % (escape(ctype), escape(object_pk)))
    except (ValueError, ValidationError), e:
        return CommentPostBadRequest("Attempting go get content-type %r and object PK %r exists raised %s" % (escape(ctype), escape(object_pk), e.__class__.__name__))


    # <Twig> Changed this part
    # Construct the comment form
    #form = comments.get_form()(target, data=data)
    form_class = get_form_class_for_object(target)
    
    form = form_class(target, data = data)
    # </Twig>

#    print "form.security_errors"

    # Check security information
#    if form.security_errors():
#        return CommentPostBadRequest("The comment form failed security verification: %s" % str(form.security_errors()) )


    # <Twig> Added this to allow custom validation
    # If there are errors or if we requested a preview show the comment
#    if form.errors or preview:
    
    # Do we want to preview the comment?
    preview = "preview" in data
    
    # Twig: Preserve the preview functionality
    if not form.validate_data(request) or preview:
#        template_list = [
#            # These first two exist for purely historical reasons.
#            # Django v1.0 and v1.1 allowed the underscore format for
#            # preview templates, so we have to preserve that format.
#            "comments/%s_%s_preview.html" % (model._meta.app_label, model._meta.module_name),
#            "comments/%s_preview.html" % model._meta.app_label,
#            # Now the usual directory based template heirarchy.
#            "comments/%s/%s/preview.html" % (model._meta.app_label, model._meta.module_name),
#            "comments/%s/preview.html" % model._meta.app_label,
#            "comments/preview.html",
#        ]
#        
#        print template_list

        from_url = data.get('from_url', None)

        # Otherwise call the view and return the data
        # @see http://djangosnippets.org/snippets/1568/
        resolver = urlresolvers.RegexURLResolver(r'^/', settings.ROOT_URLCONF)
        view, args, kwargs = resolver.resolve(from_url)
        
        if callable(view):
            form.preview = preview

            # Add the current validated form to the request object so it can be displayed correctly on the resultant page.
            request.model_comment_form = form


            # This will give the request back to the original form.
            # Ideally, the template tag will detect the request is a POST and do something with it
            return view(request, *args, **kwargs)
        else:
            # This gives a nicer error email in case it ever happens
            raise HttpResponseBadRequest('Invalid HTTP_REFERER "%s"' % from_url)
            
#        return render_to_response(
#            template_list, {
#                "comment" : form.data.get("comment", ""),
#                "form" : form,
#                "next": next,
#            },
#            RequestContext(request)
#        )
    # </Twig>

    # <Twig> This has been moved into CommentForm.clean() and modified
#    # Otherwise create the comment
#    comment = form.get_comment_object()
#    comment.ip_address = request.META.get("REMOTE_ADDR", None) # Twig: TODO: replace this with the X-REFERER address or something for transparent proxies
#    if request.user.is_authenticated():
#        comment.user = request.user
#
#    # Signal that the comment is about to be saved
#    responses = signals.comment_will_be_posted.send(
#        sender  = comment.__class__,
#        comment = comment,
#        request = request
#    )
#
#    for (receiver, response) in responses:
#        if response == False:
#            return CommentPostBadRequest(
#                "comment_will_be_posted receiver %r killed the comment" % receiver.__name__)
    # </Twig>


    # <Twig>
    comment = form.comment
    # </Twig>

    # Save the comment and signal that it was saved
    form.pre_save(request, comment)
    comment.save()
    form.post_save(request, comment)
    
    # Legacy signal
    comment_was_posted.send(
        sender  = comment.__class__,
        comment = comment,
        request = request,
    )

    # Redirect back to the original page + #comment_'comment.pk'
    redirect_url = Url(form.cleaned_data['from_url'])
    redirect_url.fragment = "c%s" % comment.pk # The name of this comment fragment is poo, but I'm sure people are using it already so no changing

    return HttpResponseRedirect(u"%s" % redirect_url)



@login_required
def mark_as_spam(request, comment_id):
    if not request.user.is_staff:
        return HttpResponseNotAllowed("You don't have sufficient access to mark this as spam.")

    comment = get_object_or_404(Comment, pk = comment_id)
    comment.is_removed = True
    comment.save()
    
    return render_to_response('comments/mark_as_spam.html', { 'comment': comment }, context_instance = RequestContext(request))
