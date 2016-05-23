from django.contrib import admin
from django.core.urlresolvers import reverse


# Register your models here.
from .models import Repository


class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('git_username', 'git_name', 'repo_synced', 'last_compiled', 'git_url', 'build_url', 'site_url')

    def build_url(self, obj):
        url = reverse('build_repo', args=(obj.git_username, obj.git_name,))
        return '<a href="%s">%s<a>' % (url, 'build')
    build_url.allow_tags = True
    build_url.short_description = 'Build link'
    
    def site_url(self, obj):
        url = reverse('visit_site', args=(obj.git_username, obj.git_name,))
        return '<a href="%s">%s<a>' % (url, 'visit')
    site_url.allow_tags = True
    site_url.short_description = 'Site link'
    
admin.site.register(Repository, RepositoryAdmin)
