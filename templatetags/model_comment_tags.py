import datetime

from inspect import isclass

from django.template import Library, TemplateSyntaxError, resolve_variable
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

from model_comments.forms import CommentForm
from model_comments.utils import get_form_class_for_object
from twigcorp.utils import ContextNode




register = Library()


@register.simple_tag
def comment_form_target():
    """
    Get the target URL for the comment form.

    Example::
        <form action="{% comment_form_target %}" method="post">
    """
    return reverse("comments-post-comment")


@register.tag
def get_comment_form(parser, token):
    """
    {% get_comment_form for [object] as [varname] %}
    """
    bits = token.split_contents()
    
    tag = bits.pop(0)
    
    if len(bits) != 4:
        raise TemplateSyntaxError('%s: Invalid arguments' % tag)
    
    bits.pop(0) # for
    obj_var = bits.pop(0)
    bits.pop(0) # as
    context_var = bits.pop(0)
    
    def wrap(context):
        obj = resolve_variable(obj_var, context)
        ctype = ContentType.objects.get_for_model(obj)
        request = context.get('request', None)

        if request is None:
            raise TemplateSyntaxError("%s: Request not found in context." % tag)
        
        form = request.model_comment_form if hasattr(request, 'model_comment_form') else None
        
        if not form:
            form_class = get_form_class_for_object(obj)

            if request.method == "POST":
                form = form_class(obj, data = request.POST.copy())
            else:
                form = form_class(obj)

        form.set_request(request)
        context[context_var] = form
        return u''
    
    return ContextNode(wrap)



@register.simple_tag
def render_comment_form(form):
    """
    Twig: Overriding this so we can render it using our own methods.

    Syntax::
        {% render_comment_form [form] %}
    """
    ctype = ContentType.objects.get_for_model(form.target_object)
    model = ctype.model_class()

    template_list = [
        # The template filename formats are identical to the way Django comment previews are.
        # Django v1.0 and v1.1 allowed the underscore format.
        # Twig: Rather than calling them previews, we just called them "form.html"
        "comments/%s_%s_form.html" % (model._meta.app_label, model._meta.module_name),
        "comments/%s_form.html" % model._meta.app_label,
        # Now the usual directory based template heirarchy.
        "comments/%s/%s/form.html" % (model._meta.app_label, model._meta.module_name),
        "comments/%s/form.html" % model._meta.app_label,
        "comments/form.html",
    ]
    
    return render_to_string(template_list, { 'form': form, })



@register.filter
def preview_comment(form):
    c = {
        'comment': form.cleaned_data,
    }
    
    ctype = ContentType.objects.get_for_model(form.target_object)
    model = ctype.model_class()
    
    # Fill in some extra stuff that's expected
    c['comment']['submit_date'] = datetime.datetime.now()

    template_list = [
            # Now the usual directory based template heirarchy.
            "comments/%s/%s/model_comment_preview.html" % (model._meta.app_label, model._meta.module_name),
            "comments/%s/model_comment_preview.html" % model._meta.app_label,
            "comments/model_comment_preview.html",
        ]
    
    return render_to_string(template_list, c)
