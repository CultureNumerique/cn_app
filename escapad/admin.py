
import os

from django.contrib import admin
from django.core.urlresolvers import reverse
from django.conf import settings

# Register your models here.
from .models import Repository
from .forms import RepositoryForm


class RepositoryAdmin(admin.ModelAdmin):
    """Custom Admin class used to administer Repository objects  """
    # fields displayed in the Repository list page admin/escapad/repository/
    list_display = ('git_url', 'show_feedback', 'repo_synced', 'default_branch', 'last_compiled',  'build_url', 'site_url', 'build_and_zip')

    # Form method we use to process some custom chekings. See forms.py
    form = RepositoryForm

    def get_readonly_fields(self, request, obj):
        """
        Method in charge of populating the readonly_fields from the list given in above attribute
        We override this method just to make the request object available in the methods defining
        the custom read-only fields below, specifically build_url_long and site_url_long
        """
        self.request = request
        # fields that won't be editable. Just remove one to make it editable
        readonly_fields = ('git_username','git_name','repo_synced','last_compiled','provider','site_url_long','build_url_long','slug')
        if obj:
            readonly_fields = ('git_url',)+readonly_fields
        return readonly_fields
        #return super(RepositoryAdmin, self).get_readonly_fields(request, obj)

    #========  custom fields  =============#
    # Below are the method used to define the custom fields, i.e those not defined in model.py
    def build_url(self, obj):
        print obj.slug
        url = reverse('build_repo', args=(obj.slug,))
        return '<a href="%s" target="_blank">%s<a>' % (url, 'build')
    build_url.allow_tags = True
    build_url.short_description = 'Build link'

    def build_and_zip(self, obj):
        url = reverse('build_zip_repo', args=(obj.slug,))
        return '<a href="%s" target="_blank">%s<a>' % (url, 'build and zip')
    build_and_zip.allow_tags = True
    build_and_zip.short_description = 'Build and zip link'

    def build_url_long(self, obj):
        """ used in detailed view """
        if obj.slug:
            url = self.request.build_absolute_uri(reverse('build_repo', args=(obj.slug,)))
            return '<a href="%s" target="_blank">%s<a>' % (url, url)
        else:
            return ''
    build_url_long.allow_tags = True
    build_url_long.short_description = 'Build link'

    def site_url(self, obj):
        url = reverse('visit_site', args=(obj.slug,))
        return '<a href="%s">%s<a>' % (url, 'visit')
    site_url.allow_tags = True
    site_url.short_description = 'Site link'

    def site_url_long(self, obj):
        if obj.slug:
            url = self.request.build_absolute_uri(reverse('visit_site', args=(obj.slug,)))
            return '<a href="%s" target="_blank">%s<a>' % (url, url)
        else:
            return ''
    site_url_long.allow_tags = True
    site_url_long.short_description = 'Site link'
    #========== End of custom fields  =================#

admin.site.register(Repository, RepositoryAdmin)
