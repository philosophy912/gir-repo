# encoding=utf8
#
# add by liaofei@bdstar.com at 2020/9/28
# generate release note between old release and current release by manifest

from __future__ import print_function
import sys
import codecs

from command import PagedCommand
from git_command import GitCommand

class Commit:
  def __init__(self, module=None,
               scope=None,
               root_cause=None,
               solution=None,
               description=None,
               title=None,
               bug_id=None):
    self.module = module
    self.scope = scope
    self.root_cause=root_cause
    self.solusion = solution
    self.description = description
    self.title = title
    self.bug_id = bug_id
    self.repository = None
    self.path = None
    self.files = None
    self.commit_id = None
    self.date = None
    self.author = None
    self.email = None
    self.change_id = None

class Releasenote(PagedCommand):
  helpUsage = """
%prog [-o --out-file] outfile [-l --last-release] last_manifest [-c --current-release] current_manifest
"""

  def _Options(self, p):
    p.add_option('-o', '--out-file',
                 dest='out_file',
                 help='The file where save the release note , which must be end with csv..',
                 metavar='-|NAME.csv')
    p.add_option('-l', '--last-release',
                 dest='last_release',
                 help='The path and name of last manifest file, eg : xx.xml',
                 metavar='-|NAME.xml')
    p.add_option('-c', '--current-release',
                 dest='current_release',
                 help='The path and name of current manifest file, eg : xx.xml',
                 metavar='-|NAME.xml')

  def __parse_description(self, contents):
    """
    单独解析提交内容部分
    :param contents:
    :param commit:
    :return:
    """
    root_flag, solution_flag, description_flag = False, False, False
    module, scope, root_cause, solution, description, title, bug_id = "", "", "", "", "", "", ""
    for content in contents:
      # feat(amapservice) : add to send NAVI_STATE_PROCESSING
      # Description:
      # add to send NAVI_STATE_PROCESSING
      if "(" in content and ")" in content and " : " in content:
        try:
          if content.startswith("Revert"):
            module = "Revert"
          elif content.startswith("fix"):
            module = "fix"
            if "#" in content:
              bug_id = content.split("#")[1].split("(")[0]
          else:
            module = content.split("(")[0]
          scope = content.split(")")[0].split("(")[1]
          title = content.split(":")[-1].strip()
        except UnicodeEncodeError:
          pass
      # 用于定位如Root Cause, Solution, Description等
      elif "Root Cause:" in content:
        root_cause = content.split(":")[1]
        root_flag = True
      elif "Solution:" in content:
        solution = content.split(":")[1]
        solution_flag = True
      elif "Description:" in content:
        description = content.split(":")[1].strip()
        description_flag = True
      else:
        if root_flag:
          root_cause = root_cause + "\n" + content
        elif solution_flag:
          solution = solution + "\n" + content
        elif description_flag:
          description = description + "\n" + content
        else:
          try:
            # 因为可能存在没有标签的情况，所以把他当成description处理
            description = description + "\n" + content
          except UnicodeDecodeError:
            print("content = " + content)

    return Commit(module=module.strip(),
                  scope=scope.strip(),
                  root_cause=root_cause.strip(),
                  solution=solution.strip(),
                  description=description.strip(),
                  title=title.strip(),
                  bug_id=bug_id.strip())

  def __filter_description(self, contents):
    """
    解析Description
    因为contents已经是去掉了空行的列表，所以只需要找到Date描述之后的数据并解析即可。
    feat(AMapService) : add AmapService
    Description:
    add AmapService
    :param contents: 内容
    :return: description的内容
    """
    descriptions = []
    flag = False
    for content in contents:
      if content.startswith("Change-Id:") or content.startswith("commit "):
        flag = False
      if flag:
        #  Mcu_App.bin | Bin 230656 -> 230656 bytes
        #  1 file changed, 0 insertions(+), 0 deletions(-)
        if not ("|" in content or "file changed" in content):
          descriptions.append(content)
      if content.startswith("Date:"):
        flag = True
    return descriptions

  def __get_commits(self, contents):
    """
    获取一次提交的数据，方便后续处理
    :param contents:
    :return:
    """
    # 所有的提交记录
    commits = []
    # 一次的提交记录
    commit = []
    # 对contents做去除空行处理
    contents = list(filter(lambda x: x != "\n", contents))
    flag = False
    for content in contents:
      content = content.replace("\n", "")
      try:
        content = content.decode("utf-8").strip()
      except UnicodeDecodeError:
        content = content.strip()
      commit.append(content)
      if content.startswith("commit "):
        if flag:
          commits.append(commit)
          commit = []
        flag = True
    # 最后一行不可能存在commit，所以要把已有的添加进去
    commits.append(commit)
    return commits

  def _get_commits(self, project, last_commit=None, curren_commit=None):
    command = ["log", "--stat", "--date=format:\'%Y-%m-%d %H:%M:%S %A\'"]
    if last_commit:
      command.append("%s..%s" % (last_commit, curren_commit))
    else:
      command.append(curren_commit)

    p = GitCommand(project, command, capture_stdout=True, capture_stderr=True)
    if p.Wait() != 0:
      print("Error when execute git log!")
      return []
    contents = p.stdout.split('\n')

    contents = self.__get_commits(contents)
    commits = []
    commit_id, commit_date, commit_author, commit_email, change_id = "", "", "", "", ""
    for one_commit in contents:
      files = []
      description = self.__filter_description(one_commit)
      commit = self.__parse_description(description)
      for line in one_commit:
        if line.startswith("commit "):
          # commit 342b7bc03d87ff41cf5ccdcfc6a6c0b7babf36cc
          commit_id = line.split(" ")[1].strip()
        if line.startswith("Date:"):
          # Date:   2020-08-19 13:25:47 星期三
          commit_date = line.replace("Date:", "").strip()
        if line.startswith("Author:"):
          # Author: guogang <guogang@chinatsp.com>
          line = line.split(":")[1]
          commit_author = line.split("<")[0].strip()
          commit_email = line.split("<")[1].replace(">", "").strip()
        if line.startswith("Change-Id:"):
          # Change-Id: I045bc0eaa048c651949fb4587ecdfa7c32876352
          change_id = line.split(":")[1].strip()
        if "|" in line:
          file_name = line.split("|")[0].strip()
          files.append(file_name)
      if commit_id == "":
        continue
      else:
        commit.repository = project.name
        commit.path = project.worktree
        commit.files = files
        commit.commit_id = commit_id
        commit.date = commit_date
        commit.author = commit_author
        commit.email = commit_email
        commit.change_id = change_id
        commits.append(commit)
    return commits

  def _Save_to_cvs(self, opt, commits):
    out_file = opt.out_file
    lines = []
    titles = "repository", "path", "commit_id", "author", "email", "date", "files", "module", "bug_id", "title", \
             "root_cause", "solution", "description", "change_id\n"
    lines.append(",".join(titles))

    for commit in commits:
      line = "%s" % commit.repository
      line += ",\"%s\"" % commit.path
      line += ",\"%s\"" % commit.commit_id
      line += ",\"%s\"" % commit.author
      line += ",\"%s\"" % commit.email
      line += ",\"%s\"" % commit.date
      line += ",\"%s\"" % commit.files
      line += ",\"%s\"" % commit.module
      line += ",\"%s\"" % commit.bug_id
      line += ",\"%s\"" % commit.title
      line += ",\"%s\"" % commit.root_cause
      line += ",\"%s\"" % commit.solusion
      line += ",\"%s\"" % commit.description
      line += ",\"%s\"\n" % commit.change_id

      lines.append(line)

    with codecs.open(out_file, 'w', 'gbk') as fp:
      fp.writelines(lines)
    fp.close()

  def _get_project_by_name(self, project_name, projects):
    for p in projects:
      if project_name == p.name:
        return p

  def _Save(self, opt, last_projects=None, current_projects=None):
    last_projects_name = []
    if last_projects:
      last_projects_name = [p.name for p in last_projects]

    # 编历最新的manifest生成 commits 信息
    commits = []
    for p in current_projects:
      if p.name == "hyp/mcu":
        continue
      if last_projects:
        current_revision = p.revisionId
        if p.name in last_projects_name:
          last_revision = self._get_project_by_name(p.name, last_projects).revisionId
          commits_in_repository = self._get_commits(p, last_commit=last_revision, curren_commit=current_revision)
        else:
          commits_in_repository = self._get_commits(p, curren_commit=current_revision)

        if commits_in_repository:
          commits += commits_in_repository

    # 提交信息写入cvs文件
    self._Save_to_cvs(opt, commits)

  def Execute(self, opt, args):
    if not opt.out_file:
      print('必需传入文件名，用于保存release note')
      sys.exit(1)

    if not opt.current_release:
      print('必需传入最新版本的manfiest文件')
      sys.exit(1)

    # 分别保存上一个版本的projects 和 当前最新的projects
    last_projects = []
    current_projects = []

    if opt.last_release:
      self.manifest.Override(opt.last_release)
      last_projects = self.GetProjects(args, missing_ok=True, submodules_ok=True)

    if opt.current_release:
      self.manifest.Override(opt.current_release)
      current_projects = self.GetProjects(args, missing_ok=True, submodules_ok=True)

    self._Save(opt, last_projects=last_projects, current_projects=current_projects)


