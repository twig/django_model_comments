from model_comments.forms import CommentForm


def get_form_class_for_object(obj):
    # Find subclasses of CommentForm and see which one we should display
    for cls in type.__subclasses__(CommentForm):
        # Instantiate class
        f = cls(obj)
        
        if f.is_form_for_object(obj):
            return cls

    # If no form, revert to default form
    return CommentForm
