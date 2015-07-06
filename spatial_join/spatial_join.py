# for MAC OSX you have to set in env:
# export PYTHONPATH=/Applications/QGIS.app/Contents/Resources/python
# for pygis to find modules

import sys
import os
import json
import boto
import pprint
from qgis.core import *
from qgis.utils import *
from qgis.gui import *
from PyQt4.QtCore import *

# globals
STATE                   = 'vic'
REPO                    = "/roll-join"
SC_EBS_DIR              = '/roll_data'
AWS_BUCKET_KEY          = 'au.com.andretrosky.roll'
AWS_DIR                 = '/winter_2015_run'
AWS_CONFIG_JSON         = STATE + AWS_DIR + '/input_config.json'
ROLL_FILE               = 'roll'
TARGETING_FILE          = STATE + AWS_DIR + '/mbtarget_DRE_EDIT_1.json'



def getFileUsingFileIndex(fileIndex, conn):
    #download the global config.json file
    #parse it and get the fileName for fileIndex

    print 'kicking the bucket'
    kickDaBucket = conn.get_bucket(AWS_BUCKET_KEY)
    print 'getting the config file'
    config = json.loads(kickDaBucket.get_key(AWS_CONFIG_JSON).get_contents_as_string())
    print 'got the config file'
    #print config
    print 'finding the rollFileName from config file'
    rollFileName = config["files"][int(fileIndex)]
    print 'got the rollFileName: %s' % rollFileName
    print 'type of rollFileName:'
    print type(rollFileName)
    
    print 'getting the actual roll for the specific rollFileName'
    rollString = (kickDaBucket.get_key(STATE + AWS_DIR + '/' + rollFileName)
                  .get_contents_as_string())
    print 'got rollString'
    
    return rollFileName, rollString 
    


def getTargetingFile(conn):
    targDict = {}
    print 'kicking the bucket'
    kickDaBucket = conn.get_bucket(AWS_BUCKET_KEY)

    print 'getting the targeting file'
    mbFileString = kickDaBucket.get_key(TARGETING_FILE).get_contents_as_string()
    print 'got mbFileString '
    
    targDict = json.loads(mbFileString)

    return targDict



def loadMeshLayer():
    #loading these files from the NFS volume, not S3.
    mLoc = SC_EBS_DIR + REPO +  "/shapefiles/" + STATE + "/MB_2011_VIC.shp"
    print mLoc
    meshLayer = QgsVectorLayer(mLoc, "mesh_layer", "ogr")
    
    if meshLayer.isValid():
        print "---> loaded meshLayer"
        #print('meshLayer.featureCount() = %d' % meshLayer.featureCount())
        #print 'meshLayer capabilities:'
        #print meshLayer.dataProvider().capabilitiesString()
        print meshLayer.metadata()
    else:
        print "ERROR: failed to load meshLayer"
        raise RuntimeError('failed to load meshLayer')
    
    features_meshLayer = meshLayer.getFeatures()

    for f in features_meshLayer:
        print '%%%%%%%%%%%%% MESH LAYERS ATTR TYPES %%%%%%%%%%%%%'
        print len(f.attributes())
        for fa in f.attributes():
            print type(fa)
        break

    print '#####################################################'

    return meshLayer



def loadDistrictLayer():
    mLoc = (SC_EBS_DIR 
	    + REPO 
	    +  "/shapefiles/" 
	    + STATE 
	    + "/Final_DistrictBoundaries_region.shp")

    print mLoc

    districtLayer = QgsVectorLayer(mLoc, "districts", "ogr")
    

    if districtLayer.isValid():
        print "---> loaded districtLayer"
        #print('districtLayer.featureCount() = %d' % districtLayer.featureCount())
        #print 'districtLayer capabilities:'
        #print districtLayer.dataProvider().capabilitiesString()
        print districtLayer.metadata()
    else:
        print "ERROR: failed to load districtLayer"
        raise RuntimeError('failed to load districtLayer')
    
    features_districtLayer = districtLayer.getFeatures()

    print 'districtLayer attribute types'
    for f in features_districtLayer:
        print '%%%%%%%%%%%%%'
        print len(f.attributes())
        for fa in f.attributes():
            print type(fa)
        break

    print '#####################################################'
   
    return districtLayer



def loadRegionLayer():
    mLoc = (SC_EBS_DIR 
	    + REPO
	    + "/shapefiles/"
	    + STATE
	    + "/Final_RegionBoundaries_region.shp")

    print mLoc

    regionLayer = QgsVectorLayer(mLoc, "districts", "ogr")

    
    if regionLayer.isValid():
        print "---> loaded regionLayer"
        #print('regionLayer.featureCount() = %d' % regionLayer.featureCount())
        #print 'regionLayer capabilities:'
        #print regionLayer.dataProvider().capabilitiesString()
        print regionLayer.metadata()
    else:
        print "ERROR: failed to load regionLayer"
        raise RuntimeError('failed to load regionLayer')
    
    
    features_regionLayer = regionLayer.getFeatures()

    print 'regionLayer attribute types'
    for f in features_regionLayer:
        print '%%%%%%%%%%%%%'
        print len(f.attributes())
        for fa in f.attributes():
            print type(fa)
        break

    print '#####################################################'

    return regionLayer



def loadFederalElectorateLayer():
    #IMPORTANT
    #federal electorate shapefile uses GDA94VICGRID94 (EGSG:3111) as its projection.
    #since this is different to all the other layers' projections, namely GDA94, it has
    #implications for when we join electorate roll to this layer.
    #we MUST do a coordRef transform to GDA94 for the geometry of all features in the 
    #federal layer

    mLoc = (SC_EBS_DIR 
	    + REPO 
	    + "/shapefiles/"
	    + STATE
	    + "/vic_24122010.shp")
    federalElectorateLayer = QgsVectorLayer(mLoc, "federalElectorate", "ogr")

    print mLoc
    
    if federalElectorateLayer.isValid():
        print "---> loaded federalElectorateLayer"
        print('federalElectorateLayer.featureCount() = %d' % federalElectorateLayer.featureCount())
        print 'federalElectorateLayer capabilities:'
        print federalElectorateLayer.dataProvider().capabilitiesString()
        print federalElectorateLayer.metadata()
    else:
        print "ERROR: failed to load federalElectorateLayer"
        raise RuntimeError('failed to load federalElectorateLayer')
    
    
    features_fedELayer = federalElectorateLayer.getFeatures()
    print 'federalElectorateLayer attribute types'
    for f in features_fedELayer:
        print '%%%%%%%%%%%%%'
        print len(f.attributes())
        for fa in f.attributes():
            print type(fa)
        break

    return federalElectorateLayer



def loadElectorateRollLayer(rollFileName):
    #use boto to download rollFileName from S3
    #parse into csv

    ### ADD A DELIMITED TEXT LAYER
    print rollFileName
    #load from the NFS volume
    uri_roll="/root/%s?delimiter=%s&xField=%s&yField=%s" % (ROLL_FILE + '_' + rollFileName, "|", "Longitude", "Latitude")
    print' yadddadadada' 
    print uri_roll 
    rollLayer = QgsVectorLayer(uri_roll, "roll", "delimitedtext")
    
    if rollLayer.isValid():
        print "---> loaded rollLayer"
        #print('rollLayer.featureCount() = %d' % rollLayer.featureCount())
        #print rollLayer.metadata()
        #print 'rollLayer capabilities:'
        #caps = rollLayer.dataProvider().capabilitiesString()
        #print caps
        #rlist = rollLayer.dataProvider().fields().toList()
        #for item in rlist:
        #    print item.name()
        #features_rollLayer = rollLayer.getFeatures()
        #print type(rollLayer) #=> qgis.core.QgsVectorLayer
        #outputs: qgis.core.QgsFeatureIterator for
        #print type(features_rollLayer)
    else:
        print "ERROR: failed to load rollLayer"
        raise RuntimeError('failed to load rollLayer')
    
    print '#####################################################'
    print '\n^^^^^ set Crs of rollLayer to GDA94 ^^^^^\n'
    
    rollLayer.setCrs(QgsCoordinateReferenceSystem(4283, QgsCoordinateReferenceSystem.EpsgCrsId))
    
    #yadda = rollLayer.getFeatures()
    #for f in yadda:
    #    print f
    #    print "Feature ID %d: " % f.id()
    #    print f.geometry()
    #    print f.geometry().wkbType()
    print '#####################################################'
    

    return rollLayer



def createMemoryLayer(rollLayer):
    ml = QgsVectorLayer("Point?crs=epsg:4283&index=yes", "mlayer", "memory")
    pr = ml.dataProvider()

    assert ml.isValid(), 'ASSERT ERROR: memory layer not valid'

    
    #print 'memLayer capablilites:'
    #print ml.dataProvider().capabilitiesString()
    
    print '\n\nAdding features to memory layer. Preparing for GIS spatial join...\n\n'
    print '#####################################################'
    
    oldAttrList = rollLayer.dataProvider().fields().toList()
    newAttrList = []
    
    #copy over the attributes from rollLayer. they are the column names
    for attr in oldAttrList:
        if ml.fieldNameIndex(attr.name()) == -1:
            newAttrList.append(QgsField(attr.name(), attr.type())) 
    
    assert len(newAttrList) > 0, 'ASSERT ERROR: attr list is empty for memory layer'
    numberOfRollAttributes = len(newAttrList)
    
    #also add in the mesh block,SA*, upper house, lower house and federal electorate
    # attributes used for spatial join
    extraAttr = ['MB_CODE11', 
		 'MB_CAT11', 
		 'SA1_MAIN11', 
		 'SA2_MAIN11', 
		 'SA2_NAME11',
                 'SA3_CODE11', 
		 'SA3_NAME11', 
		 'SA4_CODE11', 
		 'SA4_NAME11', 
		 'STE_CODE11',
                 'STE_NAME11', 
		 'GCC_CODE11', 
		 'GCC_NAME11', 
		 'VIC_LH_DISTRICT',
                 'VIC_UH_REGION', 
		 'FED_ELECT', 
		 'TARGET'
		 #'CAMP_TARGET'
		 ]

    for idx in range(0, len(extraAttr)):
        if ml.fieldNameIndex(extraAttr[idx]) == -1:
            newAttrList.append(QgsField(extraAttr[idx], QVariant.String))

    eAssertError = 'ASSERT ERROR: could not add extra attributes to mem layer'
    assert len(newAttrList) == numberOfRollAttributes + len(extraAttr), eAssertError 

    eDPError = 'ASSERT ERROR: could not add new attribute to memlayer'
    assert ml.dataProvider().addAttributes(newAttrList), eDPError 
    ml.updateFields()
    assert ml.startEditing(), 'ASSERT ERROR: unable to start editing of mem layer'

    mFeatures = []
    rFeatures = rollLayer.getFeatures()
    assert rFeatures is not None, 'ASSERT ERROR: in mem layer, rFeatures roll layer None'
    
    for rf in rFeatures:
        mFeature = QgsFeature()
        rGeometry = rf.geometry()
        mFeatureAttrs = []
        mFeatureAttrs.extend(rf.attributes())

        #dont forget to add in a dummy val for mesh block, SA*, region, district and
        #federal electorate attr
        mFeatureAttrs.append('-1')
        mFeatureAttrs.append('-1')
        mFeatureAttrs.append('-1')
        mFeatureAttrs.append('-1')
        mFeatureAttrs.append('-1')
        mFeatureAttrs.append('-1')
        mFeatureAttrs.append('-1')
        mFeatureAttrs.append('-1')
        mFeatureAttrs.append('-1')
        mFeatureAttrs.append('-1')
        mFeatureAttrs.append('-1')
        mFeatureAttrs.append('-1')
        mFeatureAttrs.append('-1')
        mFeatureAttrs.append('-1')
        mFeatureAttrs.append('-1')
        mFeatureAttrs.append('-1')
        mFeatureAttrs.append('-1')
        #mFeatureAttrs.append(None) #CAMP_TARGET default to nothing
        mFeature.setGeometry(rGeometry)
        mFeature.setAttributes(mFeatureAttrs)
        mFeatures.append(mFeature)
    

    eDPError1 = 'ASSERT ERROR: unable to add features to mem layer'
    assert ml.dataProvider().addFeatures(mFeatures), eDPError1

    return ml



def featuresDictAndSpatialIndex(ml):
    #optimization part
    print 'creating allFeatures dict and spatial index for roll...'

    #select all features along with their attributes
    allAttrs = ml.pendingAllAttributesList()
    ml.select(allAttrs)
    
    #get all features into a dictionary
    allFeatures = {}
    for gool in ml.getFeatures():
        allFeatures[gool.id()] = gool
    
    # use a spatial index on ml features to speed up join
    sIndex = QgsSpatialIndex()
    for aFeature in allFeatures.values():
        sIndex.insertFeature(aFeature)

    return allFeatures, sIndex



def joinRollToMesh(meshLayer, rollLayer, allFeatures, sIndex, memLayer, targDict):
    #we also add in TARGET vals here because we have access to mesh block vals
    print 'joining roll to mesh layer....'

    for f_mb in meshLayer.getFeatures():
        print f_mb.attribute('MB_CODE11')
    
        #some meshes could have NULL areas => boundingBox() throws exception.
        #some mb may have no geometry also.
        #check for NULL area and no geometry, if so, continue to next iteration of loop
        if not f_mb.attribute('ALBERS_SQM') or f_mb.geometry() is None:
            print 'NULL area'
            continue
    
        ids = sIndex.intersects(f_mb.geometry().boundingBox())
    
        for id in ids:
            fx = allFeatures[id]
            if fx.geometry().within(f_mb.geometry()):

                MB_match         = f_mb.attribute('MB_CODE11')
                MB_NAME_match    = f_mb.attribute('MB_CAT11')
                SA1_main_match   = f_mb.attribute('SA1_MAIN11')
                SA2_main_match   = f_mb.attribute('SA2_MAIN11')
                SA2_NAME_match   = f_mb.attribute('SA2_NAME11')
                SA3_match        = f_mb.attribute('SA3_CODE11')
                SA3_NAME_match   = f_mb.attribute('SA3_NAME11')
                SA4_match        = f_mb.attribute('SA4_CODE11')
                SA4_NAME_match   = f_mb.attribute('SA4_NAME11')
                STE_match        = f_mb.attribute('STE_CODE11')
                STE_NAME_match   = f_mb.attribute('STE_NAME11')
                GCC_match        = f_mb.attribute('GCC_CODE11')
                GCC_NAME_match   = f_mb.attribute('GCC_NAME11')
    
                #using targDict we can translate MB_match to TARGET value
                #do not assume that targDict is an exustive dict of all mesh blocks
                #in victoria.
                try:
                    #targeting is done per meshblock
                    TARGET_match     = targDict[MB_match]

                    #targeting is done per SA1
                    #TARGET_match     = targDict[SA1_main_match]
                except KeyError:
                    TARGET_match     = None
      
                MB_i             = fx.fieldNameIndex('MB_CODE11')
                MB_NAME_i        = fx.fieldNameIndex('MB_CAT11')
                SA1_main_i       = fx.fieldNameIndex('SA1_MAIN11')
                SA2_main_i       = fx.fieldNameIndex('SA2_MAIN11')
                SA2_NAME_i       = fx.fieldNameIndex('SA2_NAME11')
                SA3_i            = fx.fieldNameIndex('SA3_CODE11')
                SA3_NAME_i       = fx.fieldNameIndex('SA3_NAME11')
                SA4_i            = fx.fieldNameIndex('SA4_CODE11')
                SA4_NAME_i       = fx.fieldNameIndex('SA4_NAME11')
                STE_i            = fx.fieldNameIndex('STE_CODE11')
                STE_NAME_i       = fx.fieldNameIndex('STE_NAME11')
                GCC_i            = fx.fieldNameIndex('GCC_CODE11')
                GCC_NAME_i       = fx.fieldNameIndex('GCC_NAME11')
                TARGET_i         = fx.fieldNameIndex('TARGET')
    
    
                fattr     = {MB_i       : MB_match, 
                             MB_NAME_i  : MB_NAME_match,
                             SA1_main_i : SA1_main_match, 
                             SA2_main_i : SA2_main_match, 
                             SA2_NAME_i : SA2_NAME_match,
                             SA3_i      : SA3_match, 
                             SA3_NAME_i : SA3_NAME_match, 
                             SA4_i      : SA4_match, 
                             SA4_NAME_i : SA4_NAME_match, 
                             STE_i      : STE_match, 
                             STE_NAME_i : STE_NAME_match,
                             GCC_i      : GCC_match, 
                             GCC_NAME_i : GCC_NAME_match,
                             TARGET_i   : TARGET_match
                            }
    
                em = 'ASSERT ERROR:joinRollToMesh unable to change att vals.'
                assert memLayer.dataProvider().changeAttributeValues({fx.id(): fattr}),em



def joinRollToDistrict(distLayer, rollLayer, allFeatures, sIndex, memLayer):
    print 'joining roll to lower house districts...'

    for f_di in distLayer.getFeatures():
        print f_di.attribute('NAME')
    
        ids = sIndex.intersects(f_di.geometry().boundingBox())
    
        for id in ids:
            fx = allFeatures[id]
            #print"%s => %s"% (f_di.attribute('NAME'), fx)

            if fx.geometry().within(f_di.geometry()):
    
                DI_NAME_match    = f_di.attribute('NAME')
                DI_NAME_i        = fx.fieldNameIndex('VIC_LH_DISTRICT')
                f_di_attr        = {DI_NAME_i: DI_NAME_match}

                #print 'FOUND DI_NAME_match: %s' % DI_NAME_match

                ed = 'ASSERT ERROR:joinRollToDistrict unable to change att vals.'
                assert memLayer.dataProvider().changeAttributeValues({fx.id(): f_di_attr}), ed




def joinRollToRegion(regLayer, rollLayer, allFeatures, sIndex, memLayer):
    print 'joining roll to upper house regions...'

    for f_re in regLayer.getFeatures():
        print f_re.attribute('NAME')
    
        ids = sIndex.intersects(f_re.geometry().boundingBox())
    
        for id in ids:
            fx = allFeatures[id]
            #print"%s => %s"% (f_re.attribute('NAME'), fx)

            if fx.geometry().within(f_re.geometry()):

                RE_NAME_match    = f_re.attribute('NAME')
                RE_NAME_i        = fx.fieldNameIndex('VIC_UH_REGION')
                f_re_attr   = {RE_NAME_i: RE_NAME_match}

                er = 'ASSERT ERROR:joinRollToRegion unable to change att vals.'
                assert memLayer.dataProvider().changeAttributeValues({fx.id(): f_re_attr}), er




def joinRollToFederalElectorate(fedLayer, rollLayer, allFeatures, sIndex, memLayer):
    print 'joining roll to federal electorate...'
    ### FEDERAL ELECTORATE ###
    #this shapefile has projection of GDA94VICGRID94, EPSG:3111
    #since the memLayer is using GDA94, EGPS:4283, we must first to a projection
    #transformation before looking for intersecting geometries

    for f_fed in fedLayer.getFeatures():
        print f_fed.attribute('ELECT_DIV')

        crsSrc  = QgsCoordinateReferenceSystem(3111)      #GDA94VICGRID94
        crsDest = QgsCoordinateReferenceSystem(4283)      #GDA94
        xForm   = QgsCoordinateTransform(crsSrc, crsDest)

        # forward transformation: src -> dest
        xBoundingBox = xForm.transformBoundingBox(f_fed.geometry().boundingBox())
        assert xBoundingBox is not None, 'ASSERT ERROR: xBoundingBox is None'

        ids = sIndex.intersects(xBoundingBox)

        # need to transform the f_fed's geometry to be correct projection, GDA94
        if not f_fed.geometry().transform(xForm) == 0:
            raise RuntimeError('unable to transform federal electorate geometry')

    
        for id in ids:
            fx = allFeatures[id]
            #print"%s => %s"% (f_fed.attribute('ELECT_DIV'), fx)
                
            #now f_fed's geometry is using the GDA94 projection!
            if fx.geometry().within(f_fed.geometry()):
                FED_NAME_match    = f_fed.attribute('ELECT_DIV')
                FED_NAME_i        = fx.fieldNameIndex('FED_ELECT')
                f_fed_attr        = {FED_NAME_i: FED_NAME_match}


                ef = 'ASSERT ERROR:joinRollToFederalElectorate unable to change att vals.'
                assert memLayer.dataProvider().changeAttributeValues({fx.id(): f_fed_attr}), ef



def saveMemLayerToDisk(memLayer, rollFileName):
    print ('saving memLayer to disk...')
    joinedFileName = "roll_%s_JOINED.csv" % rollFileName[0:len(rollFileName)- 4]
    assert len(joinedFileName) > 0, 'ASSERT ERROR: joinedFileName has length zero'

    #saving to the /root dir of node
    error = QgsVectorFileWriter.writeAsVectorFormat(memLayer, "/root/" + joinedFileName, "utf-8", None, "CSV")
    
    if error == QgsVectorFileWriter.NoError:
        print "SUCCESS: wrote %s to disk" % joinedFileName
    else:
        print "ERROR: didnt write % to disk" % joinedFileName
        raise RuntimeError('failed to write memLayer to dist. Aborting.')
    
    return joinedFileName



def uploadToS3(joinedFileName, conn):
    print 'kicking the bucket to upload'
    print 'joinedFileName: %s' % joinedFileName
    kickDaBucket = conn.get_bucket(AWS_BUCKET_KEY)
    from boto.s3.key import Key
    print Key
    k = Key(kickDaBucket, joinedFileName)
    #k.key = "%s/results_full/%s" % (STATE, joinedFileName)
    k.key = "%s/%s/results_full/%s" % (STATE, AWS_DIR, joinedFileName)
    assert k.key is not None, 'ASSERT ERROR:uploadToS3 k.key is None'
    print 'key is:'
    print k
    print k.key
    print joinedFileName
    print 'setting the contents of joinedFileName to an S3 file...'

    try:
        # qgis makes a folder when saving to a path for some reason. folder is name
        # joinedFileName, so need to go into there first to find .csv file.
        k.set_contents_from_filename("/root/" + joinedFileName + "/" + joinedFileName)
        print 'SUCCESS: uploaded %s to S3' % joinedFileName
    except Exception:
       print 'ERROR: could no upload %s to S3' % joinedFileName
    



if __name__ == '__main__':
    print 'a horse is a horse of course is a horse.'

    #for OSX
    #QgsApplication.setPrefixPath("/Applications/QGIS.app/Contents/MacOS", True)

    #for Linux
    QgsApplication.setPrefixPath("/usr", True)
    
    QgsApplication.initQgis()

    #use AWS for file serving
    #make S3 connection using access keys from environment
    print 'connecting to S3...'
    conn = boto.connect_s3()
    assert conn is not None, 'ASSERT ERROR: could not connect to S3'
    print '...connected to S3'

    # find the file index which is used for determining whichi input file to work on
    fileIndex = os.environ['JOIN_FILE_INDEX'] #=> type 'str'
    assert int(fileIndex) >=0, 'ASSERT ERROR: fileIndex not given'

    rollFileName, rollString = getFileUsingFileIndex(fileIndex, conn)
    print rollFileName

    assert rollFileName is not None, 'ASSERT ERROR: rollFileName is None' 
    assert rollString   is not None, 'ASSERT ERROR: rollString is None' 

    try:
        print 'opening roll file'
        roll_file_object = open("/root/" + ROLL_FILE + '_' + rollFileName, 'w')
        roll_file_object.writelines(rollString)
    except:
        print 'ERROR: could not open roll.csv file'
        exit(1)
    finally:
        roll_file_object.close()
        

    #get the mesh block targeting file from S3
    targDict = getTargetingFile(conn)
    assert len(targDict) != 0, 'ASSERT ERROR: targDict is empty'
   

    #ADD ABS and VEC VECTOR LAYERS
    #1. state mesh layer
    #2. state district layer
    #3. state region layer
    #4. roll layer
    meshLayer = loadMeshLayer()
    distLayer = loadDistrictLayer()
    regLayer  = loadRegionLayer()
    fedLayer  = loadFederalElectorateLayer()
    rollLayer = loadElectorateRollLayer(rollFileName)

    #add a memoray layer used for spatial joining
    memLayer = createMemoryLayer(rollLayer)
    
    #optimize for speed
    allFeatures, sIndex = featuresDictAndSpatialIndex(memLayer)
    assert len(allFeatures) > 0, 'ASSERT ERROR: allFeatures dict has zero length'
    assert sIndex is not None, 'ASSERT ERROR: sIndex is None'
    print 'allFeatures dict has %d features' % len(allFeatures)

    #do spatial joining
    joinRollToMesh(meshLayer, rollLayer, allFeatures, sIndex, memLayer, targDict)
    joinRollToDistrict(distLayer, rollLayer, allFeatures, sIndex, memLayer)
    joinRollToRegion(regLayer, rollLayer, allFeatures, sIndex, memLayer)
    joinRollToFederalElectorate(fedLayer, rollLayer, allFeatures, sIndex, memLayer)

    print 'memLayer.isValid()'
    print memLayer.isValid()

    #and we're done
    joinedFileName = saveMemLayerToDisk(memLayer, rollFileName)
    print 'joinedFileName: %s' % joinedFileName
    uploadToS3(joinedFileName, conn)
