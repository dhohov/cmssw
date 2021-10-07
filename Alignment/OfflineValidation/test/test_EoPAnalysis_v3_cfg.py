REFIT = True
MISALIGN = False

if not REFIT and not MISALIGN:
    print( "Normal mode")
elif REFIT and not MISALIGN:
    print( "REFIT only MODE")
elif REFIT and MISALIGN:
    print( "REFIT + MISALIGN")
else :
    print( "ERROR! STOP!")
    exit
    
import FWCore.ParameterSet.VarParsing as VarParsing
options = VarParsing.VarParsing("analysis")

options.register ('outputRootFile',
                  "test_EOverP.root",
                  VarParsing.VarParsing.multiplicity.singleton, # singleton or list
                  VarParsing.VarParsing.varType.string,         # string, int, or float
                  "output root file")

options.register ('GlobalTag',
                  'auto:phase1_2021_realistic',
                  VarParsing.VarParsing.multiplicity.singleton,  # singleton or list
                  VarParsing.VarParsing.varType.string,          # string, int, or float
                  "Global Tag to be used")

options.parseArguments()

print( "conditionGT       : ", options.GlobalTag)
print( "outputFile        : ", options.outputRootFile)
print( "maxEvents         : ", options.maxEvents)

import FWCore.ParameterSet.Config as cms
process = cms.Process("EnergyOverMomentumTree")
    
# initialize MessageLogger and output report
process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = 1000
process.MessageLogger.TrackRefitter=dict()
    
process.options = cms.untracked.PSet( wantSummary = cms.untracked.bool(False))
    
# define input files
process.source = cms.Source("PoolSource",
                            fileNames = cms.untracked.vstring(
                                '/store/relval/CMSSW_10_6_4_patch1/RelValZEE_13/GEN-SIM-RECO/PU25ns_106X_upgrade2018_realistic_v9_HS-v1/10000/03422757-4C01-674A-A263-896DFE62A397.root',
        '/store/relval/CMSSW_10_6_4_patch1/RelValZEE_13/GEN-SIM-RECO/PU25ns_106X_upgrade2018_realistic_v9_HS-v1/10000/9C8094F1-4552-F442-9C3D-B2A81EA26A83.root',
        '/store/relval/CMSSW_10_6_4_patch1/RelValZEE_13/GEN-SIM-RECO/PU25ns_106X_upgrade2018_realistic_v9_HS-v1/10000/C49CC446-EFD3-EE44-9FEA-EA4EE081DE49.root' ))
                        
process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(options.maxEvents)
)

####################################################################
# Load  electron configuration files
####################################################################
process.load("TrackingTools.GsfTracking.GsfElectronFit_cff")

####################################################################
# Get the Magnetic Field
####################################################################
process.load('Configuration.StandardSequences.MagneticField_AutoFromDBCurrent_cff')

###################################################################
# Standard loads
###################################################################
process.load("Configuration.Geometry.GeometryRecoDB_cff")

####################################################################
# Get the BeamSpot
####################################################################
process.load("RecoVertex.BeamSpotProducer.BeamSpot_cff")

####################################################################
# Get the GlogalTag
####################################################################
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, options.GlobalTag, '')

# choose geometry
if MISALIGN:
    print( "MISALIGN")
    from CondCore.DBCommon.CondDBSetup_cfi import *
    process.trackerAlignment = cms.ESSource("PoolDBESSource",
                                            CondDBSetup,
                                            toGet = cms.VPSet(cms.PSet(record = cms.string("TrackerAlignmentRcd"),
                                                                       tag = cms.string("TrackerAlignment_2010Realistic_mc")
                                                                   )
                                                               ),
                                            connect = cms.string("sqlite_file:twist1p5.db")
                                            )
    process.es_prefer_trackerAlignment = cms.ESPrefer("PoolDBESSource", "trackerAlignment")

    process.trackerAPE = cms.ESSource("PoolDBESSource",CondDBSetup,
                                      toGet = cms.VPSet(cms.PSet(record = cms.string("TrackerAlignmentErrorRcd"),
                                                                 tag = cms.string("TrackerAlignmentErrors_2010Realistic_mc")
                                                             )
                                                    ),
                                      connect = cms.string("sqlite_file:twist1p5.db")
    )
    process.es_prefer_TrackerAPE = cms.ESPrefer("PoolDBESSource", "trackerAPE")
    
else:
    print( "NO MISALIGN")
    
# configure Gsf track refitter
if REFIT:
    print( "REFIT")
    process.load("RecoTracker.TrackProducer.TrackRefitters_cff")
    import RecoTracker.TrackProducer.TrackRefitters_cff
    process.load("TrackingTools.TransientTrack.TransientTrackBuilder_cfi")
    process.load("TrackingTools.GsfTracking.fwdGsfElectronPropagator_cff")
    process.load("RecoTracker.TrackProducer.GsfTrackRefitter_cff")
    process.GsfTrackRefitter.src = cms.InputTag('electronGsfTracks')  
    process.GsfTrackRefitter.TrajectoryInEvent = True
    process.GsfTrackRefitter.AlgorithmName = cms.string('gsf')
else:
    print( "NO REFIT")

process.load("Alignment.OfflineValidation.eopElecTreeWriter_cfi")

if REFIT:
    print( "REFIT")
    process.energyOverMomentumTree.src = cms.InputTag('GsfTrackRefitter')
else:
    print( "NO REFIT")
    process.energyOverMomentumTree.src = cms.InputTag('electronGsfTracks')
     
process.TFileService = cms.Service("TFileService",
                                   fileName = cms.string(options.outputRootFile)
                                   )
 
if REFIT:
    print( "REFIT")
    process.p = cms.Path(process.offlineBeamSpot*
                         process.GsfTrackRefitter*
                         process.energyOverMomentumTree)    
else:
    print( "NO REFIT")
    process.p = cms.Path(process.offlineBeamSpot*
                         process.energyOverMomentumTree)
