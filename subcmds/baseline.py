# encoding=utf8
#
# add by liaofei@bdstar.com at 2020/9/28
# create a new branch base on old branch(can only run on Linux & Unix),  baseline merge

from __future__ import print_function
import sys
import subprocess
import os

from command import Command
from git_command import GitCommand

USER = subprocess.Popen("git config user.name",shell=True, stdout=subprocess.PIPE).communicate()[0].strip()

class Baseline(Command):
  helpUsage = """
%prog [-o --out-file] outfile [-l --last-release] last_manifest [-c --current-release] current_manifest
"""
# self.manifest.manifestFile
  def _Options(self, p):
    p.add_option('-m', '--manifest-name',
                 dest='manifest_name',
                 help='temporary manifest to use for this work',
                 metavar='NAME.xml')
    p.add_option('-b', '--base-branch',
                 dest='base_branch',
                 help='base the branch generater a new branch')
    p.add_option('-n', '--new-branch',
                 dest='new_branch',
                 help='the new branch name')
    p.add_option('-M', '--merge-branch',
                 dest='merge_branch',
                 help='the branch which will merge into current branch')
    p.add_option('-o', '--out-file',
                 dest='out_file',
                 help='the out file save the upgrade result',
                 metavar='NAME.csv')


  def _generate_new_branch(self, opt, projects):
    # ssh -p 29418 test@10.100.193.154 gerrit create-branch $project $new_branch $base_branch
    for project in projects:
        cmd = ["ssh"]
        cmd.append("-p")
        cmd.append("29418")
        cmd.append("%s@10.100.193.154" % USER)
        cmd.append("gerrit")
        cmd.append("create-branch")
        cmd.append(project.name)
        cmd.append(opt.new_branch)
        cmd.append(opt.base_branch)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            print(err)
  def _checkoukt_branch(self, p, branch, new_branch=False):
    cmd = ["checkout"]
    if new_branch:
        cmd.append("-b")
    cmd.append(branch)
    GitCommand(p, cmd, cwd=p.worktree).Wait()

  def _baseline_upgrade(self, opt, projects):
    for project in projects:
      self._checkoukt_branch(project, self.current_branch, new_branch=True)
      self._checkoukt_branch(project, opt.merge_branch)
      self._checkoukt_branch(project, self.current_branch)
      cmd = ["merge"]
      cmd.append(opt.merge_branch)
      cmd.append("--no-edit")
      GitCommand(project, cmd, cwd=project.worktree).Wait()

  def _get_author(self, p, file):
      cmd = ["log"]
      cmd.append("--pretty=format:\"%an\"")
      cmd.append("-1")
      cmd.append(file)
      process = GitCommand(p, cmd, cwd=p.worktree, capture_stdout=True, capture_stderr=True)
      process.Wait()
      return process.stdout.strip()

  def _Save(self, opt, projects):
    out_file = os.path.join(self.manifest.repodir, "..", opt.out_file)
    lines = []
    title = '"project path", "type", "conflict", "author"\n'
    lines.append(title)

    for p in projects:
        cmd = ["status", "-s"]
        process = GitCommand(p, cmd, cwd=p.worktree, capture_stdout=True, capture_stderr=True)
        process.Wait()
        if process.stdout:
            contents = process.stdout.split('\n')
            for line in contents:
                if line.strip():
                    type = line.split()[0]
                    file = line.split()[1]
                    author = self._get_author(p, file)
                    newline = "\"%s\"" % p.relpath
                    newline += ",\"%s\"" % type
                    newline += ",\"%s\"" % file
                    newline += ",\"%s\"\n" % author
                    lines.append(newline)
        add_cmd = ["add", "."]
        GitCommand(p, add_cmd, cwd=p.worktree).Wait()

        commit_cmd = ["commit", "-m"]
        commit_cmd.append("feat(merge) : Merge all content to repository")
        GitCommand(p, commit_cmd, cwd=p.worktree).Wait()

        push_cmd = ["push", "origin"]
        push_cmd.append("%s:%s" % (self.current_branch, p.revisionExpr))
        GitCommand(p, push_cmd, cwd=p.worktree).Wait()

    with open(out_file, 'w') as fp:
        fp.writelines(lines)
    fp.close()

  def Execute(self, opt, args):
    self.current_branch = "dev_for_update_baseline"
    if opt.manifest_name:
      self.manifest.Override(opt.manifest_name)
    else:
      self.manifest.Override(self.manifest.manifestFile)

    all_projects = self.GetProjects(args, missing_ok=True, submodules_ok=True)

    if opt.base_branch and opt.new_branch:
      self._generate_new_branch(opt, all_projects)

    if opt.merge_branch:
      if not opt.out_file:
        print("Error: must assign the out file save the result")
        sys.exit(1)

      self._baseline_upgrade(opt, all_projects)

      self._Save(opt, all_projects)


