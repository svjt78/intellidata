#from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.urls import reverse

class TestPage(TemplateView):
    template_name = 'test.html'

class ThanksPage(TemplateView):
    template_name = 'thanks.html'

class HomePage(TemplateView):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse("test"))
        return super().get(request, *args, **kwargs)

class EmployeeNonStdUpload(TemplateView):
    template_name = "fileupload_form.html"



def GotoAdmin(request):
    return HttpResponseRedirect(reverse("admin:index"))
