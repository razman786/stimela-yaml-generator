##################### generated by xml-casa (v2) from applycal.xml ##################
##################### ee4997fc71a7d759055cb0074229e58f ##############################
from __future__ import absolute_import
import numpy
from casatools.typecheck import CasaValidator as _val_ctor
_pc = _val_ctor( )
from casatools.coercetype import coerce as _coerce
from casatools.errors import create_error_string
from .private.task_applycal import applycal as _applycal_t
from casatasks.private.task_logging import start_log as _start_log
from casatasks.private.task_logging import end_log as _end_log
from casatasks.private.task_logging import except_log as _except_log

class _applycal:
    """
    applycal ---- Apply calibrations solutions(s) to data

    
    Applycal reads the specified gain calibration tables or cal library,
    applies them to the (raw) data column (with the specified selection),
    and writes the calibrated results into the corrected column. This is
    done in one step, so all available calibration tables must be
    specified.
    
    Applycal will overwrite existing corrected data, and will flag data
    for which there is no calibration available.
    
    Standard data selection is supported.  See help par.selectdata for
    more information.

    --------- parameter descriptions ---------------------------------------------

    vis         Name of input visibility file
                default: non
                
                   Example: vis='ngc5921.ms'
    field       Select field using field id(s) or field name(s)
                default: '' --> all fields
                
                Use 'go listobs' to obtain the list id's or
                names. If field string is a non-negative integer,
                it is assumed a field index,  otherwise, it is
                assumed a field name.
                
                   Examples:
                   field='0~2'; field ids 0,1,2
                   field='0,4,5~7'; field ids 0,4,5,6,7
                   field='3C286,3C295'; field named 3C286 and
                   3C295
                   field = '3,4C\*'; field id 3, all names
                   starting with 4C
    spw         Select spectral window/channels
                
                Examples:
                spw='0~2,4'; spectral windows 0,1,2,4 (all
                channels)
                spw='<2';  spectral windows less than 2
                (i.e. 0,1)
                spw='0:5~61'; spw 0, channels 5 to 61,
                INCLUSIVE
                spw='\*:5~61'; all spw with channels 5 to 61
                spw='0,10,3:3~45'; spw 0,10 all channels, spw
                3, channels 3 to 45.
                spw='0~2:2~6'; spw 0,1,2 with channels 2
                through 6 in each.
                spw='0:0~10;15~60'; spectral window 0 with
                channels 0-10,15-60. (NOTE ';' to separate
                channel selections)
                spw='0:0~10^2,1:20~30^5'; spw 0, channels
                0,2,4,6,8,10, spw 1, channels 20,25,30 
                type 'help par.selection' for more examples.
    intent      Select observing intent
                default: '' (no selection by intent)
                
                   Example: intent='\*BANDPASS\*'  (selects data
                   labelled with BANDPASS intent)
    selectdata  Other data selection parameters
                default: True
    timerange   Select data based on time range
                Subparameter of selectdata=True
                default = '' (all)
                
                   Examples:
                   timerange =
                   'YYYY/MM/DD/hh:mm:ss~YYYY/MM/DD/hh:mm:ss'
                   (Note: if YYYY/MM/DD is missing date defaults
                   to first day in data set.)
                   timerange='09:14:0~09:54:0' picks 40 min on
                   first day 
                   timerange= '25:00:00~27:30:00' picks 1 hr to 3
                   hr 30min on NEXT day
                   timerange='09:44:00' pick data within one
                   integration of time
                   timerange='>10:24:00' data after this time
    uvrange     Select data within uvrange (default units meters)
                Subparameter of selectdata=True
                default: '' (all)
                
                   Examples:
                   uvrange='0~1000klambda'; uvrange from 0-1000
                   kilo-lambda
                   uvrange='>4klambda';uvranges greater than 4
                   kilolambda
    antenna     Select data based on antenna/baseline
                                   Subparameter of selectdata=True
                                   default: '' (all)
                
                                   If antenna string is a non-negative integer, it
                                   is assumed an antenna index, otherwise, it is
                                   assumed as an antenna name
                
                                       Examples: 
                                       antenna='5&6'; baseline between antenna
                                       index 5 and index 6.
                                       antenna='VA05&VA06'; baseline between VLA
                                       antenna 5 and 6.
                                       antenna='5&6;7&8'; baselines with
                                       indices 5-6 and 7-8
                                       antenna='5'; all baselines with antenna index
                                       5
                                       antenna='05'; all baselines with antenna
                                       number 05 (VLA old name)
                                       antenna='5,6,10'; all baselines with antennas
                                       5,6,10 index numbers
    scan        Scan number range
                Subparameter of selectdata=True
                default: '' = all
    observation Select by observation ID(s)
                Subparameter of selectdata=True
                default: '' = all
                
                    Example: observation='0~2,4'
    msselect    Optional complex data selection (ignore for now)
    docallib    Control means of specifying the caltables
                default: False --> Use gaintable, gainfield,
                interp, spwmap, calwt. 
                
                If True, specify a file containing cal library in
                callib
    callib      Cal Library filename
                Subparameter of callib=True
                
                If docallib=True, specify a file containing cal
                library directives
    gaintable   Gain calibration table(s) to apply on the fly
                Subparameter of callib=False
                default: '' (none)
                
                All gain table types: 'G', GSPLINE, 'T', 'B',
                'BPOLY', 'D's' can be applied.
                
                   Examples: gaintable='ngc5921.gcal'
                   gaintable=['ngc5921.ampcal','ngc5921.phcal']
    gainfield   Select a subset of calibrators from gaintable(s)
                Subparameter of callib=False
                default:'' --> all sources in table
                
                gaintable='nearest' --> nearest (on sky)
                available field in table. Otherwise, same syntax
                as field
                
                   Examples: 
                   gainfield='0~2,5' means use fields 0,1,2,5
                   from gaintable
                   gainfield=['0~3','4~6'] (for multiple
                   gaintables)
    interp      Interpolation parmameters (in time[,freq]) for each gaintable, as a list of strings.
                  Default: '' --> 'linear,linear' for all gaintable(s)
                  Options: Time: 'nearest', 'linear'
                           Freq: 'nearest', 'linear', 'cubic',
                           'spline'
                Specify a list of strings, aligned with the list of caltable specified
                in gaintable, that contain the required interpolation parameters
                for each caltable.
                
                - When frequency interpolation is relevant (B, Df,
                  Xf), separate time-dependent and freq-dependent
                  interp types with a comma (freq after the
                  comma). 
                - Specifications for frequency are ignored when the
                  calibration table has no channel-dependence. 
                - Time-dependent interp options ending in 'PD'
                  enable a "phase delay" correction per spw for
                  non-channel-dependent calibration types.
                - For multi-obsId datasets, 'perobs' can be
                  appended to the time-dependent interpolation
                  specification to enforce obsId boundaries when
                  interpolating in time. 
                - For multi-scan datasets, 'perscan' can be
                  appended to the time-dependent interpolation
                  specification to enforce scan boundaries when
                  interpolating in time. 
                - Freq-dependent interp options can have 'flag' appended
                  to enforce channel-dependent flagging, and/or 'rel' 
                  appended to invoke relative frequency interpolation
                
                     Examples: 
                     interp='nearest' (in time, freq-dep will be
                     linear, if relevant)
                     interp='linear,cubic'  (linear in time, cubic
                     in freq)
                     interp='linearperobs,splineflag' (linear in
                     time per obsId, spline in freq with
                     channelized flagging)
                     interp='nearest,linearflagrel' (nearest in
                     time, linear in freq with with channelized 
                     flagging and relative-frequency interpolation)
                     interp=',spline'  (spline in freq; linear in
                     time by default)
                     interp=['nearest,spline','linear']  (for
                     multiple gaintables)
    spwmap      Spectral windows combinations to form for gaintables(s)
                Subparameter of callib=False
                default: [] (apply solutions from each spw to
                that spw only)
                
                   Examples:
                   spwmap=[0,0,1,1] means apply the caltable
                   solutions from spw = 0 to the spw 0,1 and spw
                   1 to spw 2,3.
                   spwmap=[[0,0,1,1],[0,1,0,1]] (for multiple
                   gaintables)
    calwt       Calibrate data weights per gaintable.
                                    default: True (for all specified gaintables)
                
                                       Examples:
                                       calwt=False (for all specified gaintables)
                                       calwt=[True,False,True] (specified per
                                       gaintable)
    parang      Apply parallactic angle correction
                default: False
                
                If True, apply the parallactic angle
                correction. FOR ANY POLARIZATION CALIBRATION AND
                IMAGING, parang = True
    applymode   Calibration apply mode
                default: 'calflag' 
                Options: "calflag", "calflagstrict", "trial",
                "flagonly", "flagonlystrict", "calonly"
                
                -- applymode='calflag': calibrate data and apply
                flags from solutions
                -- applymode='trial': report on flags from
                solutions, dataset entirely unchanged
                -- applymode='flagonly': apply flags from
                solutions only, data not calibrated
                -- applymode='calonly' calibrate data only, flags
                from solutions NOT applied (use with extreme
                caution!)
                -- applymode='calflagstrict' or 'flagonlystrict'
                same as above except flag spws for which
                calibration is unavailable in one or more tables
                (instead of allowing them to pass uncalibrated
                and unflagged)
    flagbackup  Automatically back up the state of flags before the run?
                default: True

    --------- examples -----------------------------------------------------------

    
    
    For more information, see the task pages of applycal in CASA Docs:
    
    https://casa.nrao.edu/casadocs/


    """

    _info_group_ = """calibration"""
    _info_desc_ = """Apply calibrations solutions(s) to data"""

    def __call__( self, vis='', field='', spw='', intent='', selectdata=True, timerange='', uvrange='', antenna='', scan='', observation='', msselect='', docallib=False, callib='', gaintable=[  ], gainfield=[  ], interp=[  ], spwmap=[ ], calwt=[ bool(True) ], parang=False, applymode='', flagbackup=True ):
        schema = {'vis': {'type': 'cReqPath', 'coerce': _coerce.expand_path}, 'field': {'type': 'cStr', 'coerce': _coerce.to_str}, 'spw': {'type': 'cStr', 'coerce': _coerce.to_str}, 'intent': {'type': 'cStr', 'coerce': _coerce.to_str}, 'selectdata': {'type': 'cBool'}, 'timerange': {'type': 'cStr', 'coerce': _coerce.to_str}, 'uvrange': {'type': 'cVariant', 'coerce': [_coerce.to_variant]}, 'antenna': {'type': 'cStr', 'coerce': _coerce.to_str}, 'scan': {'type': 'cStr', 'coerce': _coerce.to_str}, 'observation': {'anyof': [{'type': 'cStr', 'coerce': _coerce.to_str}, {'type': 'cInt'}]}, 'msselect': {'type': 'cStr', 'coerce': _coerce.to_str}, 'docallib': {'type': 'cBool'}, 'callib': {'type': 'cStr', 'coerce': _coerce.to_str}, 'gaintable': {'type': 'cPathVec', 'coerce': [_coerce.to_list,_coerce.expand_pathvec]}, 'gainfield': {'type': 'cStrVec', 'coerce': [_coerce.to_list,_coerce.to_strvec]}, 'interp': {'type': 'cStrVec', 'coerce': [_coerce.to_list,_coerce.to_strvec]}, 'spwmap': {'type': 'cVariant', 'coerce': [_coerce.to_variant]}, 'calwt': {'type': 'cBoolVec', 'coerce': [_coerce.to_list,_coerce.to_boolvec]}, 'parang': {'type': 'cBool'}, 'applymode': {'type': 'cStr', 'coerce': _coerce.to_str, 'allowed': [ 'calonly', 'flagonlystrict', 'calflag', 'flagonly', 'trial', '', 'calflagstrict' ]}, 'flagbackup': {'type': 'cBool'}}
        doc = {'vis': vis, 'field': field, 'spw': spw, 'intent': intent, 'selectdata': selectdata, 'timerange': timerange, 'uvrange': uvrange, 'antenna': antenna, 'scan': scan, 'observation': observation, 'msselect': msselect, 'docallib': docallib, 'callib': callib, 'gaintable': gaintable, 'gainfield': gainfield, 'interp': interp, 'spwmap': spwmap, 'calwt': calwt, 'parang': parang, 'applymode': applymode, 'flagbackup': flagbackup}
        assert _pc.validate(doc,schema), create_error_string(_pc.errors)
        _logging_state_ = _start_log( 'applycal', [ 'vis=' + repr(_pc.document['vis']), 'field=' + repr(_pc.document['field']), 'spw=' + repr(_pc.document['spw']), 'intent=' + repr(_pc.document['intent']), 'selectdata=' + repr(_pc.document['selectdata']), 'timerange=' + repr(_pc.document['timerange']), 'uvrange=' + repr(_pc.document['uvrange']), 'antenna=' + repr(_pc.document['antenna']), 'scan=' + repr(_pc.document['scan']), 'observation=' + repr(_pc.document['observation']), 'msselect=' + repr(_pc.document['msselect']), 'docallib=' + repr(_pc.document['docallib']), 'callib=' + repr(_pc.document['callib']), 'gaintable=' + repr(_pc.document['gaintable']), 'gainfield=' + repr(_pc.document['gainfield']), 'interp=' + repr(_pc.document['interp']), 'spwmap=' + repr(_pc.document['spwmap']), 'calwt=' + repr(_pc.document['calwt']), 'parang=' + repr(_pc.document['parang']), 'applymode=' + repr(_pc.document['applymode']), 'flagbackup=' + repr(_pc.document['flagbackup']) ] )
        task_result = None
        try:
            task_result = _applycal_t( _pc.document['vis'], _pc.document['field'], _pc.document['spw'], _pc.document['intent'], _pc.document['selectdata'], _pc.document['timerange'], _pc.document['uvrange'], _pc.document['antenna'], _pc.document['scan'], _pc.document['observation'], _pc.document['msselect'], _pc.document['docallib'], _pc.document['callib'], _pc.document['gaintable'], _pc.document['gainfield'], _pc.document['interp'], _pc.document['spwmap'], _pc.document['calwt'], _pc.document['parang'], _pc.document['applymode'], _pc.document['flagbackup'] )
        except Exception as exc:
            _except_log('applycal', exc)
            raise
        finally:
            task_result = _end_log( _logging_state_, 'applycal', task_result )
        return task_result

applycal = _applycal( )

