#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import logging
import os

import shutil


from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from .models import Repository
from .utils import run_shell_command
logger = logging.getLogger(__name__)

class BuildView(View):
    """
    A view for generating site from Repository
    """
    http_method_names = ['get', 'post']

    @csrf_exempt  # this is needed to allow unauthenticated access to this view
    def dispatch(self, *args, **kwargs):
        return super(BuildView, self).dispatch(*args, **kwargs)

    def build_repo(self, slug, request):
        # 1. cd to repo path
        repo_path = os.path.join(settings.REPOS_DIR, slug)
        build_path = os.path.join(settings.GENERATED_SITES_DIR, slug)
        base_url = os.path.join(settings.GENERATED_SITES_URL, slug)
        logger.warn("%s | Post to build view! repo_path = %s | Base URL = %s" %
                    (timezone.now(), repo_path, base_url))

        repo_object = Repository.objects.all().filter(slug=slug)[0]
        try:
            os.chdir(repo_path)
        except Exception as e:
            return {"success": "false",
                    "reason": "repo not existing, or not synced"}

        # 2. git pull origin [branch:'master']
        git_cmds = [("git checkout %s " % repo_object.default_branch),
                    ("git pull origin %s" % repo_object.default_branch)]
        for git_cmd in git_cmds:
            success, output = run_shell_command(git_cmd)
            if not(success):
                os.chdir(settings.BASE_DIR)
                return {"success": "false", "reason": output}

        # 3. build with BASE_PATH/src/toHTML.py
        os.chdir(settings.BASE_DIR)
        feedback_option = '-f' if repo_object.show_feedback else ''
        build_cmd = ("python src/cnExport.py -ie -r %s -d %s -u %s %s -L %s" %
                     (repo_path, build_path,
                      base_url, feedback_option, settings.LOGFILE))
        success, output = run_shell_command(build_cmd)
        # go back to BASE_DIR and check output
        os.chdir(settings.BASE_DIR)
        # FIXME: output should not be displayed for security reasons,
        # since it is logged internaly to debug.log
        if success:
            repo_object.last_compiled = datetime.datetime.now()
            repo_object.save()
            return({"success": "true", "output": output})
        else:
            return {"success": "false", "reason": output}

    def post(self, request, slug, *args, **kwargs):
        res = self.build_repo(slug, request)
        return JsonResponse(res)

    def get(self, request, slug, *args, **kwargs):
        self.build_repo(slug, request)
        return redirect(reverse('visit_site', args=(slug,)))


class BuildZipView(BuildView):
    """ View for building and zipping the whole archive before returning it"""

    def get(self, request, slug, *args, **kwargs):
        built = self.build_repo(slug, request)
        if built["success"] == "true":
            build_path = os.path.join(settings.GENERATED_SITES_DIR, slug)
            archive_name = shutil.make_archive(build_path, 'zip', build_path)
            zip_file = open(archive_name, 'r')
            response = HttpResponse(zip_file,
                                    content_type='application/force-download')
            response['Content-Disposition'] = 'attachment; filename="%s.zip"' % slug
            return response
        else:
            return redirect(reverse('visit_site', args=(slug,)))


def visit_site(request, slug):
    """ Just a redirection to generated site """
    return redirect(os.path.join(settings.GENERATED_SITES_URL,
                                 slug,
                                 'index.html'))


def home(request):
    """Simple home page view"""
    # Template is in app-local folder escapad/templates/homepage.html
    return render(request, 'homepage.html', {})
