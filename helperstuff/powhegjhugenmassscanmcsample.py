import contextlib, csv, os, re, subprocess, urllib

from utilities import cache, cd, genproductions, makecards

from massscanmcsample import MassScanMCSample
from powhegjhugenmcsample import POWHEGJHUGenMCSample

class POWHEGJHUGenMassScanMCSample(MassScanMCSample, POWHEGJHUGenMCSample):
  @property
  def powhegprocess(self):
    if self.productionmode == "ggH": return "gg_H_quark-mass-effects"
    if self.productionmode == "VBF": return "VBF_H"
    if self.productionmode == "ZH": return "HZJ"
    if self.productionmode in ("WplusH", "WminusH"): return "HWJ"
    if self.productionmode == "ttH": return "ttH"
    raise ValueError("Unknown productionmode "+self.productionmode)

  @property
  def powhegsubmissionstrategy(self): return "onestep"

  @property
  def powhegcard(self):
    folder = os.path.join(genproductions, "bin", "Powheg", "production", "2017", "13TeV", "Higgs", self.powhegprocess+"_ZZ_NNPDF31_13TeV")
    folder = folder.replace("quark-mass-effects_ZZ", "ZZ_quark-mass-effects")
    makecards(folder)

    cardbase = self.powhegprocess+"_ZZ"
    cardbase = cardbase.replace("quark-mass-effects_ZZ", "ZZ_quark-mass-effects")
    if self.productionmode == "ZH": cardbase = "HZJ_HanythingJ_ZZ"
    if self.productionmode == "WplusH": cardbase = "HWplusJ_HanythingJ_ZZ"
    if self.productionmode == "WminusH": cardbase = "HWminusJ_HanythingJ_ZZ"
    if self.productionmode == "ttH": cardbase = "ttH_inclusive_ZZ"
    card = os.path.join(folder, cardbase+"_NNPDF31_13TeV_M{:d}.input".format(self.mass))

    if not os.path.exists(card):
      raise IOError(card+" does not exist")
    return card

  @property
  def powhegcardusesscript(self): return True

  @property
  def pwgrwlfilter(self):
    if self.productionmode == "ZH":
      def filter(weight):
        if weight.pdfname.startswith("NNPDF31_"): return True
        if weight.pdfname.startswith("NNPDF30_"): return True
        if weight.pdfname.startswith("PDF4LHC15"): return True
        return False
      return filter
    return super(POWHEGJHUGenMassScanMCSample, self).pwgrwlfilter

  @property
  def reweightdecay(self):
    return self.mass >= 200

  @property
  def creategridpackqueue(self):
    if self.productionmode in ("ZH", "ttH"): return "1nw"
    return super(POWHEGJHUGenMassScanMCSample, self).creategridpackqueue

  @property
  def timepereventqueue(self):
    if self.productionmode in ("ZH", "ttH"): return "1nw"
    return super(POWHEGJHUGenMassScanMCSample, self).timepereventqueue

  @property
  def filter4L(self):
    if self.decaymode != "4l": return False
    if self.productionmode in ("ggH", "VBF", "WplusH", "WminusH"): return False
    if self.productionmode in ("ZH", "ttH"): return True
    raise ValueError("Unknown productionmode "+self.productionmode)

  @property
  def doublevalidationtime(self):
    return self.productionmode in ("ZH", "ttH")

  @property
  def tarballversion(self):
    v = 1

    if self.year in (2017, 2018):
      v+=1 #JHUGen version
      if self.productionmode == "ggH" and self.decaymode == "2l2nu" and self.mass == 400: v+=1
      if self.productionmode == "ggH" and self.decaymode == "4l" and self.mass in (300, 350, 400, 450, 500, 550, 600, 700, 750, 800, 900, 1000, 1500, 2000, 2500, 3000): v+=1  #core dumps in v2
      if self.productionmode == "ggH" and self.decaymode == "2l2nu" and self.mass in (300, 400, 1000, 1500): v+=1   #core dumps in v1
      if self.productionmode == "ggH" and self.decaymode == "2l2q" and self.mass == 750: v+=1   #core dumps in v1
      if self.productionmode == "ZH" and self.decaymode == "4l" and self.mass == 145: v+=1   #core dumps in v2
      if self.decaymode == "4l": v+=1  #v1 messed up the JHUGen decay card
      if self.productionmode == "ggH" and self.decaymode == "2l2nu" and self.mass == 2500: v+=1  #v1 is corrupted
      if self.productionmode == "ggH" and self.decaymode == "2l2q" and self.mass == 800: v+=1  #same
      if self.productionmode == "ZH" and self.decaymode == "4l" and self.mass == 125: v+=1  #trimming pwg-rwl.dat
      if self.productionmode == "ZH" and self.decaymode == "4l" and self.mass in (125, 165, 170): v+=1  #same (and changing the pdfs for 125)

    if self.year == 2018:
      if self.productionmode == "ZH" and self.decaymode == "4l" and self.mass not in (125, 165, 170): v+=1  #trimming pwg-rwl.dat for these as well
      if self.productionmode == "ZH" and self.decaymode == "2l2q" and self.mass == 125: v+=1  #same

    return v

  def cvmfstarball_anyversion(self, version):
    if self.year in (2017, 2018):
      folder = os.path.join("/cvmfs/cms.cern.ch/phys_generator/gridpacks/2017/13TeV/powheg/V2", self.powhegprocess+"_ZZ_NNPDF31_13TeV")
      tarballname = os.path.basename(self.powhegcard.replace("_ZZ", "")).replace(".input", ".tgz")
      if self.decaymode != "4l":
        decaymode = self.decaymode
        if "ZZ2l2any_withtaus.input" in self.decaycard: decaymode == "2l2X"
        elif "ZZany_filter2lOSSF.input" in self.decaycard: decaymode = "_filter2l"
        tarballname = tarballname.replace("NNPDF31", "ZZ"+self.decaymode+"_NNPDF31")
      return os.path.join(folder, tarballname.replace(".tgz", ""), "v{}".format(version), tarballname)

  @property
  @cache
  def olddatasetname(self):
    p = self.productionmode
    if p == "VBF": p = "VBFH"
    with contextlib.closing(urllib.urlopen("https://raw.githubusercontent.com/CJLST/ZZAnalysis/f7d5b5fecf322a8cffa435cfbe3f05fb1ae6aba2/AnalysisStep/test/prod/samples_2016_MC.csv")) as f:
      reader = csv.DictReader(f)
      for row in reader:
        if row["identifier"] == "{}{}".format(p, self.mass):
          dataset = row["dataset"]
          result = re.sub(r"^/([^/]*)/[^/]*/[^/]*$", r"\1", dataset)
          assert result != dataset and "/" not in result, result
          if self.decaymode == "4l":
            return result
    raise ValueError("Nothing for {}".format(self))

  @property
  def datasetname(self):
    if self.decaymode == "2l2nu":
      result = type(self)(self.year, self.productionmode, "4l", self.mass).datasetname.replace("4L", "2L2Nu")
    elif self.decaymode == "2l2q":
      result = type(self)(self.year, self.productionmode, "4l", self.mass).datasetname.replace("4L", "2L2Q")
      if self.mass == 125:
        if self.productionmode in ("VBF", "WplusH", "WminusH"): result = result.replace("2L2Q", "2L2X")
        if self.productionmode == "ZH": result = "ZH_HToZZ_2LFilter_M125_13TeV_powheg2-minlo-HZJ_JHUGenV7011_pythia8"
        if self.productionmode == "ttH": result = "ttH_HToZZ_2LOSSFFilter_M125_13TeV_powheg2_JHUGenV7011_pythia8"
    elif self.productionmode in ("WplusH", "WminusH", "ZH") and self.mass > 230:
      result = type(self)(self.year, self.productionmode, self.decaymode, 230).datasetname.replace("M230", "M{:d}".format(self.mass))
    else:
      result = self.olddatasetname.replace("JHUgenV698", "JHUGenV7011").replace("JHUgenV6", "JHUGenV7011")

    pm = self.productionmode.replace("gg", "GluGlu")
    dm = self.decaymode.upper().replace("NU", "Nu")
    if self.decaymode == "2l2q" and self.mass == 125:
      if self.productionmode in ("VBF", "WplusH", "WminusH"): dm = "2L2X"
      if self.productionmode in ("ZH", "ttH"): dm = "Filter"
    searchfor = [pm, dm, "M{:d}".format(self.mass), "JHUGen"+self.JHUGenversion.replace(".", "").replace("v", "V")+"_"]
    if any(_ not in result for _ in searchfor):
      raise ValueError("Dataset name doesn't make sense:\n{}\n{}\n{}".format(result, searchfor, self))

    return result

  @property
  def JHUGenversion(self):
    if self.year in (2017, 2018):
      return "v7.0.11"
    assert False, self

  @property
  def nfinalparticles(self):
    if self.productionmode == "ggH": return 1
    if self.productionmode in ("VBF", "ZH", "WplusH", "WminusH", "ttH"): return 3
    assert False, self.productionmode

  @property
  def defaulttimeperevent(self):
    if self.productionmode in ("ggH", "VBF"): return 30
    if self.productionmode in ("WplusH", "WminusH"): return 50
    if self.productionmode == "ZH":
      if self.decaymode == "4l": return 120
      if self.decaymode == "2l2q": return 140
    if self.productionmode == "ttH":
      if self.decaymode == "4l": return 10
      if self.decaymode == "2l2q": return 10
    assert False

  @property
  def neventsfortest(self):
    if self.productionmode == "ZH": return 200
    return super(POWHEGJHUGenMassScanMCSample, self).neventsfortest

  @property
  def tags(self):
    result = ["HZZ"]
    if self.year == 2017:
      if self.productionmode in ("ggH", "VBF", "ZH", "WplusH", "WminusH", "ttH") and self.decaymode == "4l" and self.mass in (120, 125, 130):
        result.append("Fall17P1S")
      else:
        result.append("Fall17P2A")
    return result

  @property
  def genproductionscommit(self):
    return "fd7d34a91c3160348fd0446ded445fa28f555e09"

  @property
  def genproductionscommitforfragment(self):
    if self.year == 2018:
      return "7d0525c9f6633a9ee00d4e79162d82e369250ccc"
    return super(POWHEGJHUGenMassScanMCSample, self).genproductionscommitforfragment

  @classmethod
  def getmasses(cls, productionmode, decaymode):
    if decaymode == "4l":
      if productionmode in ("ggH", "VBF", "WplusH", "WminusH", "ZH"):
        return 115, 120, 124, 125, 126, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175, 180, 190, 200, 210, 230, 250, 270, 300, 350, 400, 450, 500, 550, 600, 700, 750, 800, 900, 1000, 1500, 2000, 2500, 3000
      if productionmode == "ttH":
        return 115, 120, 124, 125, 126, 130, 135, 140, 145
    if decaymode == "2l2nu":
      if productionmode in ("ggH", "VBF"):
        return 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1500, 2000, 2500, 3000
      if productionmode in ("WplusH", "WminusH", "ZH", "ttH"):
        return ()
    if decaymode == "2l2q":
      if productionmode in ("ggH", "VBF"):
        return 125, 200, 250, 300, 350, 400, 450, 500, 550, 600, 700, 750, 800, 900, 1000, 1500, 2000, 2500, 3000
      if productionmode in ("WplusH", "WminusH", "ZH", "ttH"):
        return 125,

  @classmethod
  def allsamples(cls):
    for productionmode in "ggH", "VBF", "WplusH", "WminusH", "ZH", "ttH":
      for decaymode in "4l", "2l2q", "2l2nu":
        for mass in cls.getmasses(productionmode, decaymode):
          for year in 2017, 2018:
            yield cls(year, productionmode, decaymode, mass)

  @property
  def responsible(self):
    return "hroskes"

  @property
  def nevents(self):
    if self.year == 2017:
      if self.decaymode == "4l":
        if self.productionmode == "ggH":
          if 124 <= self.mass <= 126: return 1000000
          return 500000
        elif self.productionmode in ("VBF", "ZH", "ttH"):
          if 124 <= self.mass <= 126 or self.mass >= 1500: return 500000
          return 200000
        elif self.productionmode == "WplusH":
          if 124 <= self.mass <= 126: return 300000
          return 180000
        elif self.productionmode == "WminusH":
          if 124 <= self.mass <= 126: return 200000
          return 120000
      elif self.decaymode == "2l2nu":
        if self.productionmode in ("ggH", "VBF"):
          if 200 <= self.mass <= 1000: return 250000
          elif self.mass > 1000: return 500000
      elif self.decaymode == "2l2q":
        if self.productionmode == "ggH":
          if self.mass == 125: return 1000000
          elif 200 <= self.mass <= 1000: return 200000
          elif self.mass > 1000: return 500000
        elif self.productionmode == "VBF":
          if self.mass == 125: return 500000
          elif 200 <= self.mass <= 1000: return 100000
          elif self.mass > 1000: return 500000
        elif self.productionmode in ("ZH", "ttH"):
          if self.mass == 125: return 500000
        elif self.productionmode == "WplusH":
          if self.mass == 125: return 300000
        elif self.productionmode == "WminusH":
          if self.mass == 125: return 200000
    if self.year == 2018:
      if self.decaymode == "4l":
        if self.productionmode == "ggH":
          if 105 <= self.mass <= 140: return 1000000
          return 500000
        elif self.productionmode in ("VBF", "ZH", "ttH"):
          if 105 <= self.mass <= 140 or self.mass >= 1500: return 500000
          return 200000
        elif self.productionmode == "WplusH":
          if 105 <= self.mass <= 140: return 300000
          return 180000
        elif self.productionmode == "WminusH":
          if 105 <= self.mass <= 140: return 200000
          return 120000
      elif self.decaymode == "2l2nu":
        if self.productionmode in ("ggH", "VBF"):
          if 200 <= self.mass <= 1000: return 250000
          elif self.mass > 1000: return 500000
      elif self.decaymode == "2l2q":
        if self.productionmode == "ggH":
          if self.mass == 125: return 1000000
          elif 200 <= self.mass <= 1000: return 200000
          elif self.mass > 1000: return 500000
        elif self.productionmode == "VBF":
          if self.mass == 125: return 500000
          elif 200 <= self.mass <= 1000: return 100000
          elif self.mass > 1000: return 500000
        elif self.productionmode in ("ZH", "ttH"):
          if self.mass == 125: return 500000
        elif self.productionmode == "WplusH":
          if self.mass == 125: return 300000
        elif self.productionmode == "WminusH":
          if self.mass == 125: return 200000

    raise ValueError("No nevents for {}".format(self))

  @property
  def hasnonJHUGenfilter(self): return False

  def handle_request_fragment_check_warning(self, line):
    if line.strip() == "* [WARNING] Large time/event - please check":
      if self.timeperevent <= 260 and self.productionmode == "ZH": return "ok"
      if self.timeperevent <= 165: return "ok"
    return super(POWHEGJHUGenMassScanMCSample, self).handle_request_fragment_check_warning(line)
