# -*- coding: utf-8 -*-
import logging
import os
import subprocess

from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver

from escapad.models import Repository
from escapad.utils import run_shell_command

# see in cn_app.settings.py logger declaration
logger = logging.getLogger(__name__)


# utility used by signal receivers below
def create_repo_dir(dir_name, repo_url):
    """ function to create and sync a git repo (repo_url)
        with local dir (dir_name) """
    repo_path = os.path.join(settings.REPOS_DIR, dir_name)
    current_path = os.path.abspath(os.getcwd())
    try:
        if not os.path.isdir(repo_path):
            os.makedirs(repo_path)
        else:
            run_shell_command('rm -fR %s' % repo_path)
            os.makedirs(repo_path)
        os.chdir(repo_path)
        git_cmd = ("git clone %s . --depth 1 --no-single-branch" % repo_url)
        subprocess.check_output(git_cmd.split())
    except Exception as e:
        logger.error("%s | Problem when creating and syncing dir %s with url %s \n Error : %s " %
                     ( timezone.now(), dir_name, repo_url, e))
        os.chdir(current_path)
        return False
    # In any case, go back to current_path
    os.chdir(current_path)
    logger.warning("%s | successful creation of repo %s with url %s" %
                   (timezone.now(), dir_name, repo_url))
    return True


# == signal receivers == see https://docs.djangoproject.com/en/1.10/topics/signals/#

# do this *before* saving a Repository object (either creating or editing)
@receiver(pre_save, sender=Repository)
def resync_repo_dir(sender, instance, update_fields, **kwargs):
    """ when updating a Repo, resync dir if url has changed """
    # check if being updated
    if instance.id:
        old_repo = Repository.objects.get(pk=instance.id)
        # if git_url changed, delete old dir and create new one
        if instance.git_url != old_repo.git_url:
            delete_repo_dir(old_repo)
            slug = Repository.set_slug(instance.git_url)
            create_repo_dir(slug, instance.git_url)
            return
        # FIXME if default branch changed resync it!


# do this *after* saving a Repository
@receiver(post_save, sender=Repository)
def sync_repo_dir(sender, instance, created, update_fields, **kwargs):
    """ Create a dir named [slug] and git clone [git_url] within it """
    logger.warning(" %s | creating repo dir ?= %s | update_fields = %s" %
                   (timezone.now(), created, update_fields))
    # just to avoid infinite recursion because of successive saving (see below)
    if update_fields == {'repo_synced'}:
        return
    # meaning we're creating a new record
    if created:
        instance.repo_synced = create_repo_dir(instance.slug, instance.git_url)
        instance.save(update_fields={'repo_synced'})
        return
    # updating a repo object => see above pre_save receiver
    else:
        return


# do this *after* one has deleted a Repository object
@receiver(post_delete, sender=Repository)
def delete_repo_dir(instance, **kwargs):
    """ utility function to delete repo and sites dir """
    repo_path = os.path.join(settings.REPOS_DIR, instance.slug)
    sites_path = os.path.join(settings.GENERATED_SITES_DIR, instance.slug)
    # delete repo folder and site dir for this repo
    for path in [repo_path, sites_path]:
        try:
            run_shell_command('rm -fR %s' % path)
        except Exception as e:
            logger.error("%s | Problem when deleting dir %s | error = %s" %
                         (timezone.now(), path, e))
            return False
    # delete zip if it exists:
    zip_path = sites_path+'.zip'
    try:
        if os.path.isfile(zip_path):
            run_shell_command('rm -f %s' % zip_path)
    except Exception as e:
            pass
    return True
