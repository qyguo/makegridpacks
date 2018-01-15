import abc, contextlib, glob, os, re, subprocess, urllib

from utilities import cache, cd, cdtemp, cmsswversion, genproductions, here, makecards, scramarch, wget

from mcsamplebase import MCSampleBase

class MCFMMCSample(MCSampleBase):
  @abc.abstractproperty
  def productioncard(self): pass
  @property
  def cardbase(self):
    return os.path.basename(self.productioncard).split(".DAT")[0]
  @property
  def method(self):
    "Carol fill in"
  @property
  def tmptarball(self):
    return os.path.join(here, "workdir",self.productionmode+"_"+self.decaymode, os.path.basename(self.productioncard).replace(".input", ""),
             "MCFM_%s_%s_%s_%s.tgz" % (self.method, scramarch, cmssw, self.cardbase))
  @property
  def makegridpackcommand(self):
    "Carol fill in"
  @property
  def makinggridpacksubmitsjob(self):
    return None

  @property
  @cache
  def cardsurl(self):
    commit = self.genproductionscommit
    productioncard = os.path.join("https://raw.githubusercontent.com/cms-sw/genproductions/", commit, self.productioncard.split("genproductions/")[-1])

    result = productioncard

    with cdtemp():
      wget(productioncard)
      with open(productioncard) as f:
        productiongitcard = f.read()

    with cdtemp():
      subprocess.check_output(["tar", "xvzf", self.cvmfstarball])
      if glob.glob("core.*"):
        raise ValueError("There is a core dump in the tarball\n{}".format(self))
      try:
        with open("input.DAT") as f:
          productioncard = f.read()
      except IOError:
        raise ValueError("no input.DAT in the tarball\n{}".format(self))

    if productioncard != productiongitcard:
      with cd(here):
        with open("productioncard", "w") as f:
          f.write(productioncard)
        with open("productiongitcard", "w") as f:
          f.write(productiongitcard)
      raise ValueError("productioncard != productiongitcard\n{}\nSee ./productioncard and ./productiongitcard".format(self))

    return result

  @property
  def generators(self):
    return ["MCFM701", "JHUGen v7.0.11"]

  @property
  def makegridpackscriptstolink(self):
    for filename in glob.iglob(os.path.join(genproductions, "bin", "MCFM", "*")):
      if (filename.endswith(".py") or filename.endswith(".sh") or filename.endswith("patches")) and not os.path.exists(os.path.basename(filename)):
        yield filename