import datetime

from django.contrib.comments.forms import CommentForm as DjangoCommentForm
from django.forms.util import ErrorDict
from django import forms
from django.contrib.comments.signals import comment_will_be_posted
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode
from django.conf import settings
from django.db import models
from django.template.loader import render_to_string
from django.contrib.auth.models import User

from model_comments.models import Comment
from twigcorp.utils import Url



class CommentForm(DjangoCommentForm):
    honeypot = forms.CharField(required=False, label='', widget=forms.widgets.TextInput(attrs={ 'style': 'display: none;' }))
    from_url = forms.CharField(widget=forms.HiddenInput())


    # Functions which you can safely override.
    def clean_model_comment(self, request, cleaned_data):
        """
        Twig: Do not override self.clean().
        Overriding this will allow you to do custom validation on your forms.
        
        You must returned cleaned_data.
        """
        #raise NotImplementedError("CommentForm.clean_model_comment(): You need to override this method and return cleaned_data")
        return cleaned_data


    def get_target_model(self):
        """
        Return the model type you wish to comment on.
        ie. Shirt, Store, BlogPost, etc
        """
        return models.Model


    def get_comment_model(self):
        """
        Twig: Overriding this so we know to replace the Model.
        
        Get the comment model to create with this form. Subclasses in custom
        comment apps should override this, get_comment_create_data, and perhaps
        check_for_duplicate_comment to provide custom comment models.
        """
#        raise NotImplementedError("CommentForm.get_comment_model(): You must override this.")
        return Comment


    def pre_save(self, request, comment):
        """
        Override this if you want to know when a comment is just about to be saved.
        """
        pass


    def post_save(self, request, comment):
        """
        Override this if you want to know when a comment was saved.
        """
        pass
    

    def get_comment_create_data(self):
        """
        Twig: Overrides the original one because we CAN set IP and user information into this.
        """
        return {
            'content_type': ContentType.objects.get_for_model(self.target_object),
            'object_pk': force_unicode(self.target_object._get_pk_val()),
            'user_name': self.cleaned_data["name"],
            'user_email': self.cleaned_data["email"],
            'user_url': self.cleaned_data["url"],
            'comment': self.cleaned_data["comment"],
            'submit_date': datetime.datetime.now(),
            'site_id': settings.SITE_ID,
            'is_public': True,
            'is_removed': False,
            # Twig: TODO: replace this with the X-REFERER address or something for transparent proxies
            'ip_address': self.request.META.get("REMOTE_ADDR", None),
            'user': self.request.user if self.request.user.is_authenticated() else None,
        }

    
    def is_form_for_object(self, obj):
        """
        Returns True if this form is appropriatefor the given object.
        """
        return isinstance(obj, self.get_target_model())

    # End of functions you can safely override

    
    def set_request(self, request):
        self.request = request
        
        if not self.fields['from_url'].initial:
            self.fields['from_url'].initial = str(Url(request))
        
        if request.user.is_authenticated():
            if not self.fields['name'].initial:
                self.fields['name'].initial = request.user.username
            if not self.fields['email'].initial:
                self.fields['email'].initial = request.user.email


    def is_preview(self):
        return self.is_valid() and self.preview if hasattr(self, 'preview') else False

    
    def validate_data(self, request):
        self.request = request
        return self.is_valid()


    def clean_from_url(self):
        from_url = self.cleaned_data['from_url']
        
        if not from_url:
            raise forms.ValidationError('CommentForm.clean(): from_url not set')
        
        return from_url
    
    
    def clean_comment(self):
        comment = self.cleaned_data['comment']
        
        if not comment:
            raise forms.ValidationError('Please enter a comment.')
        
        return comment
    
    
    def clean_email(self):
        email = self.cleaned_data.get('email', None)
        
        if self.request.user.is_anonymous() and not email:
            raise forms.ValidationError("Email is required for unregistered users.")

        return email

    
    def clean(self):
        """
        Implements a hefty clean() function, but this is mostly to maintain compatibility with the
        standard comments module.
        
        You should not override this. Please use the function clean_model_comment() instead.
        """
        if not hasattr(self, 'request'):
            raise forms.ValidationError("CommentForm.clean(): You must call validate_data(request)")

        
        # Do custom validation first
        cleaned_data = super(CommentForm, self).clean()
        cleaned_data = self.clean_model_comment(self.request, cleaned_data)
        
        # Prevent anonymous users masquerading as registered users
        if self.request.user.is_anonymous():
            email = cleaned_data.get('email', None)
            
            if email is None:
                raise forms.ValidationError("Unregistered users must fill in the email field.")
            
            try:
                user = User.objects.get(email__iexact=email)
                raise forms.ValidationError("This email beings to a registered user. If this is yours, please log in.")
            except User.DoesNotExist:
                pass

        # Begin sending out "pre-save" messages
        # This requires the form to be valid!
        if not self.errors:
            comment = self.get_comment_object()
            
            # Send out the original signal to maintain compatibility
            responses = comment_will_be_posted.send(
                sender=comment.__class__,
                comment=comment,
                request=self.request,
            )
    
            for (receiver, response) in responses:
                if response == False:
                    raise forms.ValidationError("comment_will_be_posted receiver %r killed the comment" % receiver.__name__)

            self.comment = comment

        return cleaned_data


    def get_comment_object(self):
        """
        Overrides this behaviour so we can call it without the form being valid.
        Reason being we can do validation checks using the original "comment_will_be_posted" within the clean method.
        This allows us to maintain compatibility with extensions such as spam filters, etc.
        """
#        if not self.is_valid():
#            raise ValueError("get_comment_object may only be called on valid forms")

        # Twig: The rest is just original code
        CommentModel = self.get_comment_model()
        new = CommentModel(**self.get_comment_create_data())
        new = self.check_for_duplicate_comment(new)

        return new


    def __unicode__(self):
        ctype = ContentType.objects.get_for_model(self.target_object)
        model = ctype.model_class()

        template_list = [
            # The template filename formats are identical to the way Django comment previews are.
            # Django v1.0 and v1.1 allowed the underscore format.
            # Twig: Rather than calling them previews, we just called them "form.html"
            "comments/%s_%s_model_comment_form.html" % (model._meta.app_label, model._meta.module_name),
            "comments/%s_model_comment_form.html" % model._meta.app_label,
            # Now the usual directory based template heirarchy.
            "comments/%s/%s/model_comment_form.html" % (model._meta.app_label, model._meta.module_name),
            "comments/%s/model_comment_form.html" % model._meta.app_label,
            "comments/model_comment_form.html",
        ]

        try:
            return render_to_string(template_list, { 'form': self, })
        except Exception, e:
            print e
        
        # Default handler
        return super(CommentForm, self).__unicode__()

    def get_model_name(self):
        return self.target_object.__class__.__name__
