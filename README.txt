#### Required
* [twigcorp.utils.ContextNode](http://twigstechtips.blogspot.com.au/2011/05/django-easy-way-for-template-tags-to.html)
* [twigcorp.utils.Url](http://twigstechtips.blogspot.com.au/2011/02/python-simple-query-string-manipulation.html)


#### Features
* First and foremost, allows you to associate various comment models to specific target models
* Link your comment models directly to the target model in ORM without any hacks like in the contrib comment module
* Allows custom validation in forms and doesn't raise 500 if fields are invalid
* Display comment previews in the current page, without having to redirect the user to a blank page
* Easier to implement pre-post comment events WITHOUT using signals
* Hooks into the contrib comment system, making it compatible with existing database/plugins/template tags/template filters
* Maintains support for the comments "comment_was_posted" signal
* Easy to theme. The model names are included in the form class names so you can specify styles for each forms.
* Easy to override templates (See below)


#### Installation
First of all, ensure that both 'model_comments' and 'django.contrib.comments' are included in INSTALLED_APPS.

However, 'model_comments' MUST be included BEFORE 'django.contrib.comments'.

Sorry, NO EXCEPTIONS.


Now, make sure in your urls.py you've replaced:
(r'^comments/', include('django.contrib.comments.urls')),

with this:
(r'^comments/', include('model_comments.urls')),


#### Implementation
For example, I have a bunch of Shirt objects I want to comment on, but I want to use a different form which contains rating/designed by/price/colour/etc.

But for any other objects (such as blog posts), I want the usual comment form.

Create a ShirtComment model to link comments to shirts.
This is where all the comment data is stored, along with 

```
from model_comments.models import Comment

class ShirtComment(Comment):
    shirt = models.ForeignKey(Shirt, related_name = 'comments', limit_choices_to = { 'display': True })
    rating = models.IntegerField()
    designed_by = models.TextField()
    # ... + any other custom data that's not already included in the contrib Comment model
```



Now to write up the comment form.
```
from model_comments.forms import CommentForm
from shirts.models import Shirt



class ShirtCommentForm(CommentForm):
    # (Optional) Use this if you wish to do any custom validation
    def clean_model_comment(self, request, cleaned_data):
        if cleaned_data['designed_by'] == 'twig':
            raise forms.ValidationError("Yo, this guy ain't no designer!")
       
        return cleaned_data


    # (Required if customising data) Defaults to django.db.models.Model
    def get_target_model(self):
        return Shirt

    
    # (Required if customising data) Defaults to model_comments.models.Comment (which is a proxy model for django.contrib.comments.models.Comment)
    def get_comment_model(self):
        return ShirtComment


    # (Optional) This allows you to fill in any data that is defined by your custom form/model
    def pre_save(self, request, comment):
        comment.shirt = comment.content_object
        comment.rating = self.cleaned_data['rating']
        comment.price = self.cleaned_data['price']
        # ... etc


    # (Optional) Easy way to detect post-comment events without using signals
    def post_save(self, request, comment):
        # TODO: send admins a nice email
        pass
```

That's it for the backend stuff.


#### Displaying

The order of the imports is important.
{% load comments %}
{% load model_comment_tags %}

(This is part of the default contrib comments module)
{% render_comment_list for shirt_obj %}

(This has the same name, but it's loaded from the model_comments module)
{% get_comment_form for shirt_obj as form %}

Display the form using this tag.
This ensures that the form is posting the correct location.
{% render_comment_form form %}



#### Theming
Well, I promised theming would be made easier.

Please note support for "preview.html" has been REMOVED.
Previews are now shown on the same page which the form is shown, and just above the form.

The files "list.html", "form.html" and "model_comment_form.html" can be placed in either:
* templates/comments/app/model/*.html (only customise template for this model)
* templates/comments/app/*.html (customise templates for all models in this app)
* templates/comments/*.html (site-wide template replacement)

To modify the styling of how the comments are displayed, override "list.html".
To modify the styling of how area around the comment form, override "form.html" (stuff like previews, 'Post a comment' label, submit/preview buttons, etc).
To modify JUST the arrangement of the form fields, override "model_comment_form.html".

Pre-Django 1.2 contrib.comment template filename formats are also supported (just like the contrib comments module).

Some examples have been placed in model_comments/templates/app/model/