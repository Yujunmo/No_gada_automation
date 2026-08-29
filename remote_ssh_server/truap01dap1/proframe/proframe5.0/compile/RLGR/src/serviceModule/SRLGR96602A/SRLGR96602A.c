/*
 * @file        SRLGR96602A.c
 * @filetype    c source file
 * @brief       제안서_대상펀드리스트
 * @author      151422
 * @version
 * @dep-header
 * @history
 *      Version:    Name :  Date :      Reference :        Desciption :
 *      --------    ------  --------    -----------        ----------------------------------
 *      VER1.00 : 151422 : 20260618 : proframe 구축     : 신규 개발
 *
 */
/*****************************************
 * KIND    : Service Module Interface
 * NODE ID : 0
 * NAME    : 제안서_대상펀드리스트
 * DESCRIPTION :
 *   SRLGR65401D
 *****************************************/
#include "SRLGR96602A.h"
static MapperMapInfo mappingInfo = {PMAP_FLAG_TRACE_ON, 0, "", "", "", ""};
#if defined (__cplusplus)
    extern "C"
#endif
long SRLGR96602A(SRLGR96602A_IN *input, SRLGR96602A_OUT *output)
{
    SRLGR96602AContext  __context;
    SRLGR96602AContext *context = &__context;
    long rc = RC_NRM;
    bzero(context, sizeof(SRLGR96602AContext));
    context->input  = input;
    context->output = output;
    {
    /*****************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 1
     * NAME    : 초기화
     * DESCRIPTION :
     *
     *****************************************/
    PFM_TRY(init_proc(context));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:INNER_MODULE_EXCEPTION NODEID1-----------
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:INNER_MODULE_EXCEPTION NODEID1-------------

    }
    {
    /*****************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 2
     * NAME    : 입력검증
     * DESCRIPTION :
     *
     *****************************************/
    PFM_TRY(input_valid_proc(context));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:INNER_MODULE_EXCEPTION NODEID2-----------
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:INNER_MODULE_EXCEPTION NODEID2-------------

    }
    {
    /*****************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 3
     * NAME    : 본처리
     * DESCRIPTION :
     *
     *****************************************/
    PFM_TRY(main_proc(context));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:INNER_MODULE_EXCEPTION NODEID3-----------
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:INNER_MODULE_EXCEPTION NODEID3-------------

    }
    {
    /*****************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 4
     * NAME    : 정상종료
     * DESCRIPTION :
     *
     *****************************************/
    PFM_TRY(norm_exit_proc(context));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:INNER_MODULE_EXCEPTION NODEID4-----------
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:INNER_MODULE_EXCEPTION NODEID4-------------

    }
    return RC_NRM;

PFM_CATCH:
    {
    /*****************************************
     * KIND    : Virtual Module
     * NODE ID : 5
     * NAME    : 예외처리
     * DESCRIPTION :
     *
     *****************************************/
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID5------------------/
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID5------------------//

    }
    return rc;
}
/*****************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 1
 * NAME    : 초기화
 * DESCRIPTION :
 *
 *****************************************/
static long init_proc(SRLGR96602AContext *context)
{
    long rc = RC_NRM;
    // User Variables Declaration
    {
    /*****************************************
     * KIND    : Virtual Module
     * NODE ID : 6
     * NAME    : 초기화
     * DESCRIPTION :
     *
     *****************************************/
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID6-----------------
    // TODO Auto-generated method stub
    STRCPY( context->prgm_id           , "SRLGR96602A"            ); //서비스ID
    STRCPY( context->lock_user_id      , SysHdrInfo_GetUser_id()  ); //사용자ID
    STRCPY( context->trns_unq_id       , SysHdrInfo_GetUser_id()  ); //출처거래고유ID
    STRCPY( context->s_proc_phcd       , "99"                     ); //처리단계코드(99:기타)
    STRCPY( context->s_btch_bzwr_dncd  , "ZZ"                     ); //배치업무구분코드(SP:기준가)
    pfmGetDate(context, context->prgm_date);
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID6-------------------

    }
    return RC_NRM;

PFM_CATCH:
    return rc;
}
/*****************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 2
 * NAME    : 입력검증
 * DESCRIPTION :
 *
 *****************************************/
static long input_valid_proc(SRLGR96602AContext *context)
{
    long rc = RC_NRM;
    // User Variables Declaration
    {
    /*****************************************
     * KIND    : Virtual Module
     * NODE ID : 7
     * NAME    : 입력값 검증
     * DESCRIPTION :
     *
     *****************************************/
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID7-----------------
    // TODO Auto-generated method stub
    // 입력구조체 필수(가능한한 필수 기술요망)
    NOT_NULL_PRINT_SRLGR96602A_IN(INPUT);

    /* INPUT Struct Member에 대한 Validation 을 표준 코딩형태로 파신한다.
     * UI 필수 조건에 의해 정삭하여 사용하시면 됩니다.
     */
    PFM_CHECK_ISZERO( INPUT->data_evnt_proc_hndl
                     , "ZCOM00001"
                     , "데이터이벤트처리취급"
                     ); // 01 : 데이터이벤트처리취급
    PFM_CHECK_ISSPNULL( INPUT->mncm_code
                       , "ZCOM00001"
                       , "운용사코드"
                       ); // 03 : 운용사코드

    /* YYYYMMDD 포맷의 문자열을 입력받아 정합성 체크.  TRUE  : legal case  */
    /*                                                FALSE : illegal case*/
    rc = pfmIsValidDate( INPUT->strn_date); /* 시작일자 */
    if (rc == FALSE) {
        PFM_ERR("날짜형 문자열 오류 %s  rc : [%ld]", "ZCOM00001", "시작일자");
        PFM_SET_ERR("ZCOM00001", pfmDateGetErrorMsg(), rc);
        return RC_ERR;
    } // 04 : 시작일자

    rc = pfmIsValidDate( INPUT->end_date); /* 종료일자 */
    if (rc == FALSE) {
        PFM_ERR("날짜형 문자열 오류 %s  rc : [%ld]", "ZCOM00001", "종료일자");
        PFM_SET_ERR("ZCOM00001", pfmDateGetErrorMsg(), rc);
        return RC_ERR;
    } // 05 : 종료일자

    STRCPY(OUTPUT->proc_rslt_cntn , "");
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID7-------------------

    }
    return RC_NRM;

PFM_CATCH:
    return rc;
}
/*****************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 3
 * NAME    : 본처리
 * DESCRIPTION :
 *
 *****************************************/
static long main_proc(SRLGR96602AContext *context)
{
    long rc = RC_NRM;
    // User Variables Declaration
    {
    /*****************************************
     * KIND    : Intermediary Module Block
     * NODE ID : 56
     * NAME    : 배치실행
     * DESCRIPTION :
     *
     *****************************************/
    // Variables Declaration
    char ls_proc_rslt_dncd[1 + 1];
    // User Variables Declaration
    // Variables Initialization
    bzero(ls_proc_rslt_dncd, sizeof(ls_proc_rslt_dncd));
    {
    /*****************************************
     * KIND    : DBIO Call
     * NODE ID : 8
     * NAME    : ZCOM_서비스_버튼_로그기본_제안서_배치실행 조회_VS701
     * DESCRIPTION :
     *
     *****************************************/
    TRU_SRVC_BTN_LB_VS701In  temporaryInput;
    TRU_SRVC_BTN_LB_VS701Out temporaryOutput;
    bzero(&temporaryInput,  sizeof(TRU_SRVC_BTN_LB_VS701In));
    bzero(&temporaryOutput, sizeof(TRU_SRVC_BTN_LB_VS701Out));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID11-------
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID11---------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID11------------------
    // TODO Auto-generated method stub
    STRCPY(temporaryInput.mncm_code    , INPUT->mncm_code            ); //운용사코드
    STRCPY(temporaryInput.prgm_id      , context->prgm_id            ); //프로그램ID
    STRCPY(temporaryInput.lock_user_id , INPUT->otis_use_code        ); //대상구분(사용자ID)
    STRCPY(temporaryInput.otis_use_code, "ALL"                       ); //처리을
    STRCPY(temporaryInput.prgm_date    , context->prgm_date          );
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID11--------------------

    /*****************************************
     * KIND              : DBIO Callee Info
     * NAME              : ZCOM_서비스_버튼_로그기본_제안서_배치실행 조회_VS701
     * EXEC              : SELECT
     * INPUT             : TRU_SRVC_BTN_LB_VS701In
     * OUTPUT            : TRU_SRVC_BTN_LB_VS701Out
     * ARRAY INPUT       : NONE
     * ARRAY OUTPUT      : NONE
     * DYNAMIC STRUCTURE : NONE
     *****************************************/
    PFM_TRYNJ(pfmDbioSelect("TRU_SRVC_BTN_LB_VS701", &temporaryInput, &temporaryOutput));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_EXCEPTION NODEID11----------------
    /* 단건 Select 예외처리 */
    if( rc != RC_NRM) {
        PFM_ERR( "[FAIL] DBIO error [%ld][%s]"
               , PDB_ERRORNUM
               , PDB_ERRORSTR
               );
        /* ZCOM00005 : 조회처리 중 오류가 발생하였습니다.[DB오류코드:%ld]. 시스템담당자에게 문의하세요. */
        PFM_SET_ERR( "ZCOM00005"
                   , PDB_ERRORNUM
                   );
        /* ZCOM00145 : 데이터 조회 중 오류발생. [%s], [%ld][%s] */
        PFM_SET_ADD_ERR( "ZCOM00145"
                        , "TRU_SRVC_BTN_LB_VS701"
                        , PDB_ERRORNUM
                        , PDB_ERRORSTR
                        );
        return RC_ERR;
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_EXCEPTION NODEID11------------------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:AFTER_CODE NODEID11--------------------
    // TODO Auto-generated method stub
    STRCPY(ls_proc_rslt_dncd     , temporaryOutput.proc_rslt_dncd);
    STRCPY(OUTPUT->proc_rslt_cntn, ls_proc_rslt_cntn);
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:AFTER_CODE NODEID11----------------------

    }
    if(
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE_CONDITION NODEID10-----
        STRCMP(ls_proc_rslt_dncd , "N") == 0
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE_CONDITION NODEID10-------
    )
    {
    /*****************************************
     * KIND    : Virtual Module
     * NODE ID : 10
     * NAME    : 배치가 실행중
     * DESCRIPTION :
     *
     *****************************************/
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID10----------------
    // TODO Auto-generated method stub
    PFM_DBG("# 배치가 실행중 입니다.  ");
    //PFM_ERR("배치가 실행중 입니다.  ");
    //PFM_SET_ERR("RLGR00021");
    STRCPY(OUTPUT->proc_rslt_cntn , ls_proc_rslt_cntn);
    return RC_NRM;
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID10------------------

    }
    {
    /*****************************************
     * KIND    : Intermediary Module Block
     * NODE ID : 22
     * NAME    : 배치실행진행
     * DESCRIPTION :
     *
     *****************************************/
    // Variables Declaration
    TRU_CMN_SRCH_SLCT_TM_EI001In inStr_TRU_CMN_SRCH_SLCT_TM_EI001[1000];
    long ll_ins_idx = 0; /* insert 입력구조체 순번 */
    // User Variables Declaration
    bzero(inStr_TRU_CMN_SRCH_SLCT_TM_EI001, sizeof(inStr_TRU_CMN_SRCH_SLCT_TM_EI001));
    {
    /*****************************************
     * KIND    : Module Call
     * NODE ID : 21
     * NAME    : 시퀀스 채번 조회
     * DESCRIPTION :
     *
     *****************************************/
    MZCOM_GetSeqNo_IN  temporaryInput;
    MZCOM_GetSeqNo_OUT temporaryOutput;
    bzero(&temporaryInput,  sizeof(MZCOM_GetSeqNo_IN));
    bzero(&temporaryOutput, sizeof(MZCOM_GetSeqNo_OUT));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID21------------------
    // TODO Auto-generated method stub
    STRCPY( temporaryInput.seq_obj_nm , "TRU_CMN_SRCH_SLCT_TM_SQ01" ); // 01 : 시퀀스 채번 조회
    STRCPY( temporaryInput.seq_pf_cd  , "C"                         ); // 02 :
    temporaryInput.seq_tot_len        = 16                          ; // 03 :

    /* 비즈모듈 입출력구조체 Debug출력 */
    PRINT_MZCOM_GetSeqNo_IN(&temporaryInput);
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID21--------------------

    /*****************************************
     * KIND    : Module Callee Info
     * NAME    : 시퀀스 채번 조회
     * INPUT   : MZCOM_GetSeqNo_IN
     * OUTPUT  : MZCOM_GetSeqNo_OUT
     *****************************************/
    PFM_TRYNJ(pfmDlCall("MZCOM_GetSeqNo", "MZCOM_GetSeqNo", &temporaryInput, &temporaryOutput));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:MODULE_EXCEPTION NODEID21-------------
    if (rc == RC_NFD) {
        PFM_ERR( "[FAIL] 비즈니스 모듈 호출 오류(MZCOM_GetSeqNo)  rc : [%ld]", rc);
        /* ZCOM00003 : 해당 조건의 데이터가 없습니다. */
        PFM_SET_ERR( "ZCOM00003" );
        /* ZCOM00156 : 모듈 수행시 오류가 발생하였습니다. "MZCOM_GetSeqNo" */
        PFM_SET_ADD_ERR( "ZCOM00156"
                        , "MZCOM_GetSeqNo"
                        , PDB_ERRORNUM
                        , PDB_ERRORSTR
                        );
        return RC_ERR;
    }
    else {
        PFM_ERR( "[FAIL] 비즈니스 모듈 호출 오류(MZCOM_GetSeqNo)  rc : [%ld]", rc);
        /* ZCOM00005 : 조회처리 중 오류가 발생하였습니다.[DB오류코드:%ld]. 시스템담당자에게 문의하세요. */
        PFM_SET_ERR( "ZCOM00005"
                   , PDB_ERRORNUM
                   );
        /* ZCOM00156 : 모듈 수행시 오류가 발생하였습니다. "MZCOM_GetSeqNo" */
        PFM_SET_ADD_ERR( "ZCOM00156"
                        , "MZCOM_GetSeqNo"
                        , PDB_ERRORNUM
                        , PDB_ERRORSTR
                        );
        return RC_ERR;
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:MODULE_EXCEPTION NODEID21---------------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:AFTER_CODE NODEID21-------------------
    // TODO Auto-generated method stub
    STRCPY( context->code_slct_grp_no, temporaryOutput.seq_next_no );
    PRINT_MZCOM_GetSeqNo_OUT(&temporaryOutput);
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:AFTER_CODE NODEID21---------------------

    }
    {
    /*****************************************
     * KIND    : DBIO Fetch Loop
     * NODE ID : 12
     * NAME    : PSTP_펀드_정보_이력_배치생성_다건조회Fetch Loop
     * DESCRIPTION :
     *
     *****************************************/
    PFO_FUND_INFR_HT_VF721In  temporaryInput12;
    PFO_FUND_INFR_HT_VF721Out temporaryOutput12[1000];
    bzero(&temporaryInput12, sizeof(PFO_FUND_INFR_HT_VF721In));
    bzero(temporaryOutput12, sizeof(PFO_FUND_INFR_HT_VF721Out) * 1000);
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID14------
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID14--------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID14------------------
    // TODO Auto-generated method stub
    STRCPY( temporaryInput12.mncm_code , INPUT->mncm_code  );
    STRCPY( temporaryInput12.strn_date , INPUT->strn_date  );
    STRCPY( temporaryInput12.end_date  , INPUT->end_date   );
    STRCPY( temporaryInput12.fund_code , "*"               );
    STRCPY( temporaryInput12.trst_dncd , "*"                );
    STRCPY( temporaryInput12.trteco_code, "*"                );
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID14--------------------

    /*****************************************
     * KIND              : DBIO_FETCH Callee Info
     * NAME              : PSTP_펀드_정보_이력_배치생성_다건조회
     * EXEC              : FETCH
     * INPUT             : PFO_FUND_INFR_HT_VF721In
     * OUTPUT            : PFO_FUND_INFR_HT_VF721Out
     * ARRAY INPUT       : NONE
     * ARRAY OUTPUT      : PSTP_펀드_정보_이력_배치생성_다건조회
     * DYNAMIC STRUCTURE : NONE
     *****************************************/
    PFM_TRYNJ(pfmDbioOpenCursorArray("PFO_FUND_INFR_HT_VF721", &temporaryInput12));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:FETCH_LOOP_OPEN_EXCEPTION NODEID12----
    if(PDB_CHK_FAIL) {
        PFM_ERR("Cursor open error DBIO[%s], ERR_NO[%ld], ERR_STR[%s]", "PSTP_펀드_정보_이력_배치생성_다건조회", PDB_ERRORNUM, PDB_ERRORSTR);
        return rc;
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:FETCH_LOOP_OPEN_EXCEPTION NODEID12------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:FETCH_LOOP_PRE NODEID12---------------
    context->tot_cnt    = 0;
    context->cur_cnt    = 0;
    context->loop_status = TRUE;
    while (context->loop_status)
    {
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:FETCH_LOOP_PRE NODEID12-----------------
        {
        PFM_TRYNJ(pfmDbioFetchCursorArray("PFO_FUND_INFR_HT_VF721", 1000, &temporaryOutput12));
        //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_FETCH_EXCEPTION NODEID14-----
        if(rc != RC_NRM)
        {
            if(rc == RC_NFD)
            {
                if(PDB_RECNUM == 0)
                {
                    /* 조회조건에 맞는 값이 없음 */
                    PFM_ERR("[FAIL] DBIO : Fetch data not found!!! ");
                    /* ZCOM00003 : 해당 조건의 데이터가 없습니다. */
                    PFM_SET_ERR("ZCOM00003");
                    return RC_NRM;
                }
                /* 한번에 Fetch 한 건수가 Fetch Array Size 보다 작을 경우는 loop 탈출 후 이후 전체누적 DATA 건수[%ld] 로 처리 */
                context->loop_status = FALSE;
            }
            else
            {
                PFM_ERR("[FAIL] DBIO : error [%ld][%s]", PDB_ERRORNUM, PDB_ERRORSTR);
                /* ZCOM00005 : 조회처리 중 오류가 발생하였습니다.[DB오류코드:%ld]. 시스템담당자에게 문의하세요. */
                PFM_SET_ERR("ZCOM00005", PDB_ERRORNUM);
                /* ZCOM00145 : 데이터 조회 중 오류발생. [%s], [%ld][%s] */
                PFM_SET_ADD_ERR("ZCOM00145", "PFO_FUND_INFR_HT_VF721", PDB_ERRORNUM, PDB_ERRORSTR);
                pfmDbioCloseCursorArray("PFO_FUND_INFR_HT_VF721");
                return RC_ERR;
            }
        }
        context->cur_cnt = PDB_RECNUM - context->tot_cnt;
        context->tot_cnt = PDB_RECNUM;
        //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_FETCH_EXCEPTION NODEID14-------

        //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:AFTER_CODE NODEID14--------------
        // TODO Auto-generated method stub
        //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:AFTER_CODE NODEID14----------------

        }
        {
        /*****************************************
         * KIND    : Loop Module
         * NODE ID : 24
         * NAME    : 입력 루프
         * DESCRIPTION :
         *
         *****************************************/
        //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:LOOP_MODULE_PRE NODEID24--------
        for(context->loop_idx = 0; context->loop_idx < context->cur_cnt; context->loop_idx++)
        {
        //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:LOOP_MODULE_PRE NODEID24----------
            {
            /*****************************************
             * KIND    : Virtual Module
             * NODE ID : 28
             * NAME    : 입력처리구조체설정
             * DESCRIPTION :
             *
             *****************************************/
            //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID28------
            /* 개발자 코딩 : 다건처리를 위한 입력구조체를 설정한다. */
            /* ll_ins_idx == 0 이거나 DBIO의 입력구조체 크기와 같다면, 입력구조체와 사용 인덱스 변수를 초기화한다. */
            PFM_DBG("ll_ins_idx[%ld] :: AS_TRU_CMN_SRCH_SLCT_TM_EI001[%ld]"
                   , ll_ins_idx
                   , AS_TRU_CMN_SRCH_SLCT_TM_EI001
                   );
            if ( 0 == ll_ins_idx
              || 0 == ( ll_ins_idx % AS_TRU_CMN_SRCH_SLCT_TM_EI001)
               ) {

                bzero(&inStr_TRU_CMN_SRCH_SLCT_TM_EI001, sizeof(inStr_TRU_CMN_SRCH_SLCT_TM_EI001));
                ll_ins_idx = 0;
            }
            /* 개발자 코딩 : 로컬에 선언된 입력구조체 배열에 값을 매핑한다. */
            STRCPY( inStr_TRU_CMN_SRCH_SLCT_TM_EI001[ll_ins_idx].code_slct , context->code_slct_grp_no );
            STRCPY( inStr_TRU_CMN_SRCH_SLCT_TM_EI001[ll_ins_idx].mncm_code , temporaryOutput12[context->loop_idx].mncm_code );
            STRCPY( inStr_TRU_CMN_SRCH_SLCT_TM_EI001[ll_ins_idx].clmn_id  , temporaryOutput12[context->loop_idx].fund_code );
            STRCPY( inStr_TRU_CMN_SRCH_SLCT_TM_EI001[ll_ins_idx].dtl_code , temporaryOutput12[context->loop_idx].fund_code );
            STRCPY( inStr_TRU_CMN_SRCH_SLCT_TM_EI001[ll_ins_idx].st1_dtl_code , temporaryOutput12[context->loop_idx].trst_dncd );
            STRCPY( inStr_TRU_CMN_SRCH_SLCT_TM_EI001[ll_ins_idx].nd2_dtl_code , temporaryOutput12[context->loop_idx].trteco_code );
            STRCPY( inStr_TRU_CMN_SRCH_SLCT_TM_EI001[ll_ins_idx].th3_dtl_code , "" );
            STRCPY( inStr_TRU_CMN_SRCH_SLCT_TM_EI001[ll_ins_idx].th4_dtl_code , "" );
            STRCPY( inStr_TRU_CMN_SRCH_SLCT_TM_EI001[ll_ins_idx].th5_dtl_code , "" );
            STRCPY( inStr_TRU_CMN_SRCH_SLCT_TM_EI001[ll_ins_idx].th6_dtl_code , "" );
            STRCPY( inStr_TRU_CMN_SRCH_SLCT_TM_EI001[ll_ins_idx].th7_dtl_code , "" );
            STRCPY( inStr_TRU_CMN_SRCH_SLCT_TM_EI001[ll_ins_idx].th8_dtl_code , "" );
            STRCPY( inStr_TRU_CMN_SRCH_SLCT_TM_EI001[ll_ins_idx].th9_dtl_code , "" );
            STRCPY( inStr_TRU_CMN_SRCH_SLCT_TM_EI001[ll_ins_idx].th10_dtl_code, "" );

            SET_DB_INSERT_INFO(&inStr_TRU_CMN_SRCH_SLCT_TM_EI001[ll_ins_idx]);

            ll_ins_idx++;
            //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID28--------

            }
            {
            /*****************************************
             * KIND    : Intermediary Module Block
             * NODE ID : 27
             * NAME    : 처리로직
             * DESCRIPTION :
             *  01.입력구조체 순번이(입력구조체 크기)와 같거나,
             *  02.처리루프의 마지막이 데이터가 존재한다.
             *****************************************/
            // User Variables Declaration
            if(
            //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE_CONDITION NODEID29
                ll_ins_idx == AS_TRU_CMN_SRCH_SLCT_TM_EI001
             || ( context->loop_idx == ( context->cur_cnt - 1) ) && 0 < ll_ins_idx
            //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE_CONDITION NODEID29-
            )
            {
            /*****************************************
             * KIND    : DBIO Call
             * NODE ID : 29
             * NAME    : 공통검색선택임시 코드선택 다건입력
             * DESCRIPTION :
             *
             *****************************************/
            TRU_CMN_SRCH_SLCT_TM_EI001Out temporaryOutput;
            bzero(&temporaryOutput, sizeof(TRU_CMN_SRCH_SLCT_TM_EI001Out));
            //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID29-
            // TODO Auto-generated method stub
            //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID29---

            //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID29-----------
            // TODO Auto-generated method stub
            //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID29-------------

            /*****************************************
             * KIND              : DBIO Callee Info
             * NAME              : 공통검색선택임시 코드선택 다건입력
             * EXEC              : INSERT
             * INPUT             : TRU_CMN_SRCH_SLCT_TM_EI001In
             * OUTPUT            : TRU_CMN_SRCH_SLCT_TM_EI001Out
             * ARRAY INPUT       : 공통검색선택임시 코드선택 다건입력
             * ARRAY OUTPUT      : NONE
             * DYNAMIC STRUCTURE : NONE
             *****************************************/
            PFM_TRYNJ(pfmDbioDmlArray("TRU_CMN_SRCH_SLCT_TM_EI001", ll_ins_idx, inStr_TRU_CMN_SRCH_SLCT_TM_EI001, &temporaryOutput, NULL, PFMDBIO_NOLOCK));
            //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_EXCEPTION NODEID29-------
            if( rc != RC_NRM) /* DBIO ERROR 처리 */
            {
                if( rc == RC_DUP){
                    PFM_ERR( "[FAIL] DBIO : insert data duplicate. is already exist!!!" );
                    /* ZCOM00007 : 요청한 데이터가 이미 존재합니다. */
                    PFM_SET_ERR( "ZCOM00007" );
                    /* ZCOM00146 : 데이터 등록 중 오류발생. [%s], [%ld][%s] */
                    PFM_SET_ADD_ERR( "ZCOM00146"
                                    , "TRU_CMN_SRCH_SLCT_TM_EI001"
                                    , PDB_ERRORNUM
                                    , PDB_ERRORSTR
                                    );
                    return RC_ERR;
                }
                else{
                    /* DBIO 오류 */
                    PFM_ERR( "[FAIL] DBIO error [%ld][%s]"
                           , PDB_ERRORNUM
                           , PDB_ERRORSTR
                           );
                    /* ZCOM00008 : 데이터 등록 중 오류가 발생하였습니다.[DB오류코드:%ld]. */
                    PFM_SET_ERR( "ZCOM00008", PDB_ERRORNUM );
                    /* ZCOM00146 : 데이터 등록 중 오류발생. [%s], [%ld][%s] */
                    PFM_SET_ADD_ERR( "ZCOM00146"
                                    , "TRU_CMN_SRCH_SLCT_TM_EI001"
                                    , PDB_ERRORNUM
                                    , PDB_ERRORSTR
                                    );
                    return RC_ERR;
                }
            }
            //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_EXCEPTION NODEID29---------

            //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:AFTER_CODE NODEID29-----------
            // TODO Auto-generated method stub
            //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:AFTER_CODE NODEID29-------------

            }
            } // TRU_CMN_SRCH_SLCT_TM_EI001 Loop End
        //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:LOOP_MODULE_POST NODEID24-------
        }
        //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:LOOP_MODULE_POST NODEID24---------

        }
    }
    //END_OF_CODE:PSTP_펀드_정보_이력_배치생성_다건조회Fetch Loop DBIO_FETCH_LOOP

    PFM_TRY(pfmDbioCloseCursorArray("PFO_FUND_INFR_HT_VF721"));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_FETCH_LOOP_CLOSE_EXCEPTION NODEID12-
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_FETCH_LOOP_CLOSE_EXCEPTION NODEID12---

    }
    {
    /*****************************************
     * KIND    : Intermediary Module Block
     * NODE ID : 15
     * NAME    : JOB ID 생성
     * DESCRIPTION :
     *
     *****************************************/
    // User Variables Declaration
    {
    /*****************************************
     * KIND    : Module Call
     * NODE ID : 16
     * NAME    : 작업편드생성처리
     * DESCRIPTION :
     *
     *****************************************/
    MMCMP_ProcJobFundCrtn_IN  temporaryInput;
    MMCMP_ProcJobFundCrtn_OUT temporaryOutput;
    bzero(&temporaryInput,  sizeof(MMCMP_ProcJobFundCrtn_IN));
    bzero(&temporaryOutput, sizeof(MMCMP_ProcJobFundCrtn_OUT));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID16------------------
    STRCPY( temporaryInput.mncm_code       , INPUT->mncm_code            );
    STRCPY( temporaryInput.proc_date       , SysHdrInfo_GetSyst_date()   );
    STRCPY( temporaryInput.user_id         , SysHdrInfo_GetUser_id()     );
    STRCPY( temporaryInput.proc_phcd       , context->s_proc_phcd        );
    STRCPY( temporaryInput.btch_bzwr_dncd  , context->s_btch_bzwr_dncd   );
    STRCPY( temporaryInput.code_slct_grp_no, context->code_slct_grp_no   );
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID16--------------------

    /* 비즈모듈 입출력구조체 Debug출력 */
    NOT_NULL_PRINT MMCMP_ProcJobFundCrtn_IN(&temporaryInput);
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:MODULE_EXCEPTION NODEID16-------------

    /*****************************************
     * KIND    : Module Callee Info
     * NAME    : 작업편드생성처리
     * INPUT   : MMCMP_ProcJobFundCrtn_IN
     * OUTPUT  : MMCMP_ProcJobFundCrtn_OUT
     *****************************************/
    PFM_TRYNJ(pfmDlCall("MMCMP_ProcJobFundCrtn", "MMCMP_ProcJobFundCrtn", &temporaryInput, &temporaryOutput));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:MODULE_EXCEPTION NODEID16-------------
    if( rc == RC_NFD) {
        /* 자료가 없을 시 업무에 알맞게 정상하고 처리한다. */
        PFM_ERR( "[FAIL] 비즈니스 모듈 호출 오류(MMCMP_ProcJobFundCrtn)  Fetch Data Not Found 오류" );
        /* ZCOM00003 : 해당 조건의 데이터가 없습니다. */
        PFM_SET_ERR( "ZCOM00003" );
        /* ZCOM00156 : 모듈 수행시 오류가 발생하였습니다. "MMCMP_ProcJobFundCrtn" */
        PFM_SET_ADD_ERR( "ZCOM00156"
                        , "MMCMP_ProcJobFundCrtn"
                        , PDB_ERRORNUM
                        , PDB_ERRORSTR
                        );
        return RC_ERR;
    }
    else{
        /* 모듈 호출시의 업무에 따른 알맞은 메시지 처리(에러, 정상 처리결정) */
        PFM_ERR( "[FAIL] 비즈니스 모듈 호출 오류(MMCMP_ProcJobFundCrtn)  rc : [%ld]", rc);
        /* ZCOM00005 : 조회처리 중 오류가 발생하였습니다.[DB오류코드:%ld]. 시스템담당자에게 문의하세요. */
        PFM_SET_ERR( "ZCOM00005" );
        /* ZCOM00156 : 모듈 수행시 오류가 발생하였습니다. "MMCMP_ProcJobFundCrtn" */
        PFM_SET_ADD_ERR( "ZCOM00156"
                        , "MMCMP_ProcJobFundCrtn"
                        , PDB_ERRORNUM
                        , PDB_ERRORSTR
                        );
        return RC_ERR;
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:MODULE_EXCEPTION NODEID16---------------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:AFTER_CODE NODEID16-------------------
    // TODO Auto-generated method stub
    STRCPY(context->job_id, temporaryOutput.job_id);
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:AFTER_CODE NODEID16---------------------

    }
    {
    /*****************************************
     * KIND    : DBIO Call
     * NODE ID : 17
     * NAME    : ZCOM_서비스_버튼_로그기본_제안서_MAX순번_단건조회
     * DESCRIPTION :
     *
     *****************************************/
    TRU_SRVC_BTN_LB_VS001In  temporaryInput;
    TRU_SRVC_BTN_LB_VS001Out temporaryOutput;
    bzero(&temporaryInput,  sizeof(TRU_SRVC_BTN_LB_VS001In));
    bzero(&temporaryOutput, sizeof(TRU_SRVC_BTN_LB_VS001Out));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID18------
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID18--------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID18------------------
    // TODO Auto-generated method stub
    STRCPY(temporaryInput.mncm_code    , INPUT->mncm_code   );
    STRCPY(temporaryInput.proc_date    , context->strn_date );
    STRCPY(temporaryInput.srvc_code    , context->prgm_id   );
    STRCPY(temporaryInput.btn_ensn_name, context->job_id    );
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID18--------------------

    /*****************************************
     * KIND              : DBIO Callee Info
     * NAME              : ZCOM_서비스_버튼_로그기본_제안서_MAX순번_단건조회
     * EXEC              : SELECT
     * INPUT             : TRU_SRVC_BTN_LB_VS001In
     * OUTPUT            : TRU_SRVC_BTN_LB_VS001Out
     * ARRAY INPUT       : NONE
     * ARRAY OUTPUT      : NONE
     * DYNAMIC STRUCTURE : NONE
     *****************************************/
    PFM_TRYNJ(pfmDbioSelect("TRU_SRVC_BTN_LB_VS001", &temporaryInput, &temporaryOutput));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_EXCEPTION NODEID18----------------
    if ( (rc != RC_NRM) && (rc != RC_NFD)) /* DBIO 오류 */
    {
        PFM_ERR( "[FAIL] DBIO error [%ld][%s]", PDB_ERRORNUM, PDB_ERRORSTR);
        /* ZCOM00005 : 조회처리 중 오류가 발생하였습니다.[DB오류코드:%ld]. 시스템담당자에게 문의하세요. */
        PFM_SET_ERR("ZCOM00005", PDB_ERRORNUM, PDB_ERRORSTR);
        return RC_ERR;
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_EXCEPTION NODEID18------------------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:AFTER_CODE NODEID18--------------------
    // TODO Auto-generated method stub
    STRCPY(context->job_id, temporaryOutput.job_id); // 배치실행순번
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:AFTER_CODE NODEID18----------------------

    }
    {
    /*****************************************
     * KIND    : Intermediary Module Block
     * NODE ID : 13
     * NAME    : 배치실행저장
     * DESCRIPTION :
     *
     *****************************************/
    // User Variables Declaration
    if( rc == RC_NFD)
    {
        context->seq = 1;
    }
    else
    {
        context->seq = temporaryOutput.seq;
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID13-------------------

    {
    /*****************************************
     * KIND    : DBIO Call
     * NODE ID : 23
     * NAME    : ZCOM_서비스_버튼_로그기본_제안서_PI701
     * DESCRIPTION :
     *
     *****************************************/
    TRU_SRVC_BTN_LB_PI701In  temporaryInput;
    TRU_SRVC_BTN_LB_PI701Out temporaryOutput;
    bzero(&temporaryInput,  sizeof(TRU_SRVC_BTN_LB_PI701In));
    bzero(&temporaryOutput, sizeof(TRU_SRVC_BTN_LB_PI701Out));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID23------
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID23--------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID23------------------
    /* INSERT시 관리용컬럼 세팅 매크로 */
    SET_DB_INSERT_INFO(&temporaryInput);
    STRCPY(temporaryInput.mncm_code     , INPUT->mncm_code            );
    STRCPY(temporaryInput.proc_date     , context->prgm_date          );
    STRCPY(temporaryInput.srvc_code     , context->prgm_id            );
    STRCPY(temporaryInput.btn_ensn_name , context->job_id             );
    temporaryInput.seq                  = context->seq                ;
    STRCPY(temporaryInput.rmrk          , context->job_id             );
    STRCPY(temporaryInput.msg_cntn      , ""                          );
    STRCPY(temporaryInput.proc_user_id  , context->lock_user_id       );
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID23--------------------

    /*****************************************
     * KIND              : DBIO Callee Info
     * NAME              : ZCOM_서비스_버튼_로그기본_제안서_PI701
     * EXEC              : INSERT
     * INPUT             : TRU_SRVC_BTN_LB_PI701In
     * OUTPUT            : TRU_SRVC_BTN_LB_PI701Out
     * ARRAY INPUT       : NONE
     * ARRAY OUTPUT      : NONE
     * DYNAMIC STRUCTURE : NONE
     *****************************************/
    PFM_TRYNJ(pfmDbioDml1("TRU_SRVC_BTN_LB_PI701", &temporaryInput, &temporaryOutput, NULL, PFMDBIO_NOLOCK));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_EXCEPTION NODEID23----------------
    if( rc != RC_NRM)
    {
        if( rc == RC_DUP){
            PFM_ERR( "[FAIL] DBIO : insert data duplicate. is already exist!!!" );
            /* ZCOM00007 : 요청한 데이터가 이미 존재합니다. */
            PFM_SET_ERR( "ZCOM00007" );
            return RC_ERR;
        }
        else{
            PFM_ERR( "[FAIL] DBIO error [%ld][%s]", PDB_ERRORNUM, PDB_ERRORSTR);
            /* ZCOM00008 : 데이터 등록 중 오류가 발생하였습니다. Insert시 DBIO에서 오류가 발생하였습니다.[DB오류코드:%ld] */
            PFM_SET_ERR( "ZCOM00008", PDB_ERRORNUM );
            return RC_ERR;
        }
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_EXCEPTION NODEID23------------------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:AFTER_CODE NODEID23--------------------
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:AFTER_CODE NODEID23----------------------

    }
    }
    {
    /*****************************************
     * KIND    : Intermediary Module Block
     * NODE ID : 57
     * NAME    : 생성자료 삭제
     * DESCRIPTION :
     *
     *****************************************/
    // User Variables Declaration
    {
    /*****************************************
     * KIND    : DBIO Call
     * NODE ID : 61
     * NAME    : RLGR_RLGR_임시 삭제
     * DESCRIPTION :
     *
     *****************************************/
    RPT_RLGR_TM_ED001In  temporaryInput;
    RPT_RLGR_TM_ED0010ut temporaryOutput;
    bzero(&temporaryInput,  sizeof(RPT_RLGR_TM_ED001In));
    bzero(&temporaryOutput, sizeof(RPT_RLGR_TM_ED0010ut));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID61------
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID61--------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID61------------------
    // TODO Auto-generated method stub
    STRCPY(temporaryInput.mncm_code   , INPUT->mncm_code       ); // 01 : 운용사코드
    STRCPY(temporaryInput.prgm_id     , context->prgm_id       ); // 02 : 프로그램ID
    STRCPY(temporaryInput.lock_user_id, context->lock_user_id  ); // 03 : 사용자ID
    STRCPY(temporaryInput.trns_unq_id , context->trns_unq_id   ); // 04 : 거래고유ID

    PRINT_RPT_RLGR_TM_ED001In(&temporaryInput);
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID61--------------------

    /*****************************************
     * KIND              : DBIO Callee Info
     * NAME              : RLGR_RLGR_임시 삭제
     * EXEC              : DELETE
     * INPUT             : RPT_RLGR_TM_ED001In
     * OUTPUT            : RPT_RLGR_TM_ED0010ut
     * ARRAY INPUT       : NONE
     * ARRAY OUTPUT      : NONE
     * DYNAMIC STRUCTURE : NONE
     *****************************************/
    PFM_TRYNJ(pfmDbioDml1("RPT_RLGR_TM_ED001", &temporaryInput, &temporaryOutput, NULL, PFMDBIO_NOLOCK));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_EXCEPTION NODEID61----------------
    /* 단건 Delete 예외처리 */
    if( rc != RC_NRM) {
        if( rc != RC_NFD){
            /* DBIO 오류 */
            PFM_ERR( "[FAIL] DBIO error [%ld][%s]", PDB_ERRORNUM, PDB_ERRORSTR);
            /* RC_NFD시의 업무에 따른 다른 알맞은 메시지 처리(에러, 정상 처리결정) */
            SPRINTF( context->buf_dtl_msg
                   , "보고서임시테이블 삭제중 오류가 발생 하였습니다. [%ld] [%s]"
                   , PDB_ERRORNUM
                   , PDB_ERRORSTR
                   );
            /* ZCOM00014 : 삭제중 오류가 발생 하였습니다. */
            PFM_SET_ERR( "ZCOM00014"
                       , context->buf_dtl_msg
                       ); // 맞는 유형의 에러메시지 코드 작성
            return RC_ERR;
        }
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_EXCEPTION NODEID61------------------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:AFTER_CODE NODEID61--------------------
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:AFTER_CODE NODEID61----------------------

    }
    }
    {
    /*****************************************
     * KIND    : Virtual Module
     * NODE ID : 58
     * NAME    : Arguments 편집
     * DESCRIPTION :
     *
     *****************************************/
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID58-----------------
    // TODO Auto-generated method stub
    SPRINTF(   context->btch_input
           , "%s;%s;%s;%s;%s;%ld;%s;%s;"
           , INPUT->mncm_code       //운용사코드
           , INPUT->strn_date       //시작일
           , INPUT->end_date        //종료일
           , INPUT->otis_use_code   //대외기관
           , INPUT->prgm_id         //프로그램ID
           , context->job_id        //배치일순위단위구분
           );

    PFM_LOG('I', ">>> %s  운용사 %s;%s;%ld;%s;%s;" BRLGRPRP0001 제안서 Call.......", context->btch_input);
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID58-------------------

    }
    {
    /*****************************************
     * KIND    : Module Call
     * NODE ID : 60
     * NAME    : 온라인배치 호출
     * DESCRIPTION :
     *
     *****************************************/
    MZPFM_BatchLinkCall_IN  temporaryInput;
    MZPFM_BatchLinkCall_OUT temporaryOutput;
    bzero(&temporaryInput,  sizeof(MZPFM_BatchLinkCall_IN));
    bzero(&temporaryOutput, sizeof(MZPFM_BatchLinkCall_OUT));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID60------------------
    /* 호출 배치코드(대문자) */
    STRCPY(temporaryInput.bat_code, "BRLGRPRP0001");
    /* 호출 배치 아규먼트 */
    STRCAT(temporaryInput.bat_call_type, "A");
    /*-------------------------------------------------*/
    /*   호출 배치 아규먼트                              */
    /*-------------------------------------------------*/
    STRCPY(temporaryInput.args_ctnt, context->btch_input);

    PRINT_MZPFM_BatchLinkCall_IN(&temporaryInput);
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID60--------------------

    /*****************************************
     * KIND    : Module Callee Info
     * NAME    : 온라인배치 호출
     * INPUT   : MZPFM_BatchLinkCall_IN
     * OUTPUT  : MZPFM_BatchLinkCall_OUT
     *****************************************/
    PFM_TRYNJ(pfmDlCall("MZPFM_BatchLinkCall", "MZPFM_BatchLinkCall", &temporaryInput, &temporaryOutput));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:MODULE_EXCEPTION NODEID60-------------
    if( rc != RC_NRM){
        /* ZCOM00016 : [%s] 호출 중 오류가 발생하였습니다. */
        PFM_SET_ERR("ZCOM00016", "MZPFM_BatchLinkCall");
        /* ZCOM00016 */
        PFM_SET_ERR("ZCOM00016", pfmGetErrMsg());
        return RC_ERR;
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:MODULE_EXCEPTION NODEID60---------------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:AFTER_CODE NODEID60-------------------
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:AFTER_CODE NODEID60---------------------

    }
    }
    {
    /*****************************************
     * KIND    : Intermediary Module Block
     * NODE ID : 19
     * NAME    : 임시테이블조회
     * DESCRIPTION :
     *
     *****************************************/
    // User Variables Declaration
    if(
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:INNER_MODULE_CONDITION NODEID19------
        INPUT->data_evnt_proc_hndl == DATA_PROC_SEL
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:INNER_MODULE_CONDITION NODEID19--------
    )
    {
    /*****************************************
     * KIND    : DBIO Fetch Loop
     * NODE ID : 19
     * NAME    : RLGR_RLGR_임시(제안서_대상펀드리스트) 다건조회Fetch Loop
     * DESCRIPTION :
     *
     *****************************************/
    RPT_RLGR_TM_VF701In  temporaryInput87;
    RPT_RLGR_TM_VF701Out temporaryOutput87[100];
    bzero(&temporaryInput87, sizeof(RPT_RLGR_TM_VF701In));
    bzero(temporaryOutput87, sizeof(RPT_RLGR_TM_VF701Out) * 100);
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID88------
    // TODO Auto-generated method stub
    STRCPY( temporaryInput87.mncm_code  , INPUT->mncm_code      ); // 01 :
    STRCPY( temporaryInput87.prgm_id    , context->prgm_id      ); // 02 :
    STRCPY( temporaryInput87.user_id    , context->lock_user_id ); // 03 :
    STRCPY( temporaryInput87.trns_unq_id, context->trns_unq_id  ); // 04 :
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID88--------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID88------------------
    // TODO Auto-generated method stub
    PFM_PAGING_DBIO_BF(AS_SRLGR96602A_OUT_GRID01, &temporaryInput87, INPUT->last_num01);
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID88--------------------

    /*****************************************
     * KIND              : DBIO_FETCH Callee Info
     * NAME              : RLGR_RLGR_임시(제안서_대상펀드리스트) 다건조회
     * EXEC              : FETCH
     * INPUT             : RPT_RLGR_TM_VF701In
     * OUTPUT            : RPT_RLGR_TM_VF701Out
     * ARRAY INPUT       : NONE
     * ARRAY OUTPUT      : RPT_RLGR_TM_VF701BundleOut
     * DYNAMIC STRUCTURE : NONE
     *****************************************/
    PFM_TRYNJ(pfmDbioOpenCursorArray("RPT_RLGR_TM_VF701", &temporaryInput87));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_FETCH_LOOP_OPEN_EXCEPTION NODEID87
    if(PDB_CHK_FAIL) {
        PFM_ERR("Cursor open error DBIO[%s], ERR_NO[%ld], ERR_STR[%s]", "RLGR_RLGR_임시(제안서_대상펀드리스트) 다건조회", PDB_ERRORNUM, PDB_ERRORSTR);
        return rc;
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_FETCH_LOOP_OPEN_EXCEPTION NODEID87--

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:FETCH_LOOP_PRE NODEID87---------------
    context->tot_cnt     = 0;
    context->cur_cnt     = 0;
    context->loop_status = TRUE;
    while (context->loop_status)
    {
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:FETCH_LOOP_PRE NODEID87-----------------
        {
        PFM_TRYNJ(pfmDbioFetchCursorArray("RPT_RLGR_TM_VF701", 100, &temporaryOutput87));
        //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_FETCH_EXCEPTION NODEID88-----
        if(rc != RC_NRM)
        {
            if(rc == RC_NFD)
            {
                if(PDB_RECNUM == 0)
                {
                    /* 조회조건에 맞는 값이 없음 */
                    PFM_ERR("[FAIL] DBIO : Fetch data not found!!! ");
                    SPRINTF( context->buf_dtl_msg
                           , "제안서 다건조회 데이터가 존재하지 않습니다. [RPT_RLGR_TM_VF701] 다건조회 중 오류가 발생하였습니다."
                           );
                    /* ZCOM00003 : 해당 조건의 데이터가 없습니다. */
                    PFM_SET_ERR("ZCOM00003", PDB_ERRORNUM);
                    pfmDbioCloseCursorArray("RPT_RLGR_TM_VF701"); /* Cursor close */
                    return RC_NRM;
                }
                /* 한번에 Fetch 한 건수가 Fetch Array Size 보다 작을 경우는 loop 탈출 후 이후 전체누적 DATA 건수로 처리 */
                context->loop_status = FALSE;
            }
            else
            {
                PFM_ERR("[FAIL] DBIO : error [%ld][%s]", PDB_ERRORNUM, PDB_ERRORSTR);
                /* ZCOM00005 : 조회처리 중 오류가 발생하였습니다.[DB오류코드:%ld]. 시스템담당자에게 문의하세요. */
                PFM_SET_ERR("ZCOM00005", PDB_ERRORNUM);
                pfmDbioCloseCursorArray("RPT_RLGR_TM_VF701"); /* Cursor close */
                return rc;
            }
        }
        context->cur_cnt = PDB_RECNUM - context->tot_cnt;
        context->tot_cnt = PDB_RECNUM;
        //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_FETCH_EXCEPTION NODEID88-------

        //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:AFTER_CODE NODEID88--------------
        // TODO Auto-generated method stub
        //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:AFTER_CODE NODEID88----------------

        }
        {
        /*****************************************
         * KIND    : Virtual Module
         * NODE ID : 26
         * NAME    : 출력값없음 처리
         * DESCRIPTION :
         *
         *****************************************/
        //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID26----------
        for(context->loop_idx = 0; context->loop_idx < context->cur_cnt; context->loop_idx++)
        {
            /* FETCH 한 건수가 출력 그리드의 최대 배열 크기보다 커지면 루프를 탈출한다. */
            if(context->tot_cnt >= AS_SRLGR96602A_OUT_GRID01)
            {
                PFM_DBG( "조회 건수가 출력 그리드의 최대 배열 크기보다 커지면 루프를 탈출한다.  " );
                context->loop_status = FALSE;
                break;
            }
            // 출력데이터 설정
            PRINT_RPT_RLGR_TM_VF701Out(&temporaryOutput87[context->loop_idx]);

            STRCPY( OUTPUT->grid01[context->tot_cnt].st1_ltrs_cntn , temporaryOutput87[context->loop_idx].st1_ltrs_cntn );
            STRCPY( OUTPUT->grid01[context->tot_cnt].nd2_ltrs_cntn , temporaryOutput87[context->loop_idx].nd2_ltrs_cntn );
            STRCPY( OUTPUT->grid01[context->tot_cnt].th3_ltrs_cntn , temporaryOutput87[context->loop_idx].th3_ltrs_cntn );
            STRCPY( OUTPUT->grid01[context->tot_cnt].th4_ltrs_cntn , temporaryOutput87[context->loop_idx].th4_ltrs_cntn );
            STRCPY( OUTPUT->grid01[context->tot_cnt].th5_ltrs_cntn , temporaryOutput87[context->loop_idx].th5_ltrs_cntn );
            STRCPY( OUTPUT->grid01[context->tot_cnt].th6_ltrs_cntn , temporaryOutput87[context->loop_idx].th6_ltrs_cntn );
            STRCPY( OUTPUT->grid01[context->tot_cnt].st1_date      , temporaryOutput87[context->loop_idx].st1_date      );
            STRCPY( OUTPUT->grid01[context->tot_cnt].nd2_date      , temporaryOutput87[context->loop_idx].nd2_date      );

            OUTPUT->grid01[context->tot_cnt].st1_ntgr_amt = temporaryOutput87[context->loop_idx].st1_ntgr_amt;
            OUTPUT->grid01[context->tot_cnt].nd2_ntgr_amt = temporaryOutput87[context->loop_idx].nd2_ntgr_amt;
            OUTPUT->grid01[context->tot_cnt].th3_ntgr_amt = temporaryOutput87[context->loop_idx].th3_ntgr_amt;
            OUTPUT->grid01[context->tot_cnt].th4_ntgr_amt = temporaryOutput87[context->loop_idx].th4_ntgr_amt;
            OUTPUT->grid01[context->tot_cnt].th5_ntgr_amt = temporaryOutput87[context->loop_idx].th5_ntgr_amt;
            OUTPUT->grid01[context->tot_cnt].th6_ntgr_amt = temporaryOutput87[context->loop_idx].th6_ntgr_amt;
            OUTPUT->grid01[context->tot_cnt].th7_ntgr_amt = temporaryOutput87[context->loop_idx].th7_ntgr_amt;
            OUTPUT->grid01[context->tot_cnt].th8_ntgr_amt = temporaryOutput87[context->loop_idx].th8_ntgr_amt;
            OUTPUT->grid01[context->tot_cnt].th9_ntgr_amt = temporaryOutput87[context->loop_idx].th9_ntgr_amt;

            OUTPUT->grid01[context->tot_cnt].st1_dcpn_number_amt = temporaryOutput87[context->loop_idx].st1_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].nd2_dcpn_number_amt = temporaryOutput87[context->loop_idx].nd2_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th9_dcpn_number_amt  = temporaryOutput87[context->loop_idx].th9_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th10_dcpn_number_amt = temporaryOutput87[context->loop_idx].th10_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th11_dcpn_number_amt = temporaryOutput87[context->loop_idx].th11_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th12_dcpn_number_amt = temporaryOutput87[context->loop_idx].th12_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th13_dcpn_number_amt = temporaryOutput87[context->loop_idx].th13_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th14_dcpn_number_amt = temporaryOutput87[context->loop_idx].th14_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th15_dcpn_number_amt = temporaryOutput87[context->loop_idx].th15_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th16_dcpn_number_amt = temporaryOutput87[context->loop_idx].th16_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th17_dcpn_number_amt = temporaryOutput87[context->loop_idx].th17_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th18_dcpn_number_amt = temporaryOutput87[context->loop_idx].th18_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th19_dcpn_number_amt = temporaryOutput87[context->loop_idx].th19_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th20_dcpn_number_amt = temporaryOutput87[context->loop_idx].th20_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th21_dcpn_number_amt = temporaryOutput87[context->loop_idx].th21_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th22_dcpn_number_amt = temporaryOutput87[context->loop_idx].th22_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th23_dcpn_number_amt = temporaryOutput87[context->loop_idx].th23_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th24_dcpn_number_amt = temporaryOutput87[context->loop_idx].th24_dcpn_number_amt;

            // 229211
            // 229992 박준기 20200804
            OUTPUT->grid01[context->tot_cnt].th25_dcpn_number_amt = temporaryOutput87[context->loop_idx].th25_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th26_dcpn_number_amt = temporaryOutput87[context->loop_idx].th26_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th27_dcpn_number_amt = temporaryOutput87[context->loop_idx].th27_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th28_dcpn_number_amt = temporaryOutput87[context->loop_idx].th28_dcpn_number_amt;

            // 항목추가
            // - 2016.09.10 : 이성민 요청
            //이성민 추가 20170905
            OUTPUT->grid01[context->tot_cnt].th29_dcpn_number_amt = temporaryOutput87[context->loop_idx].th29_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th30_dcpn_number_amt = temporaryOutput87[context->loop_idx].th30_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th31_dcpn_number_amt = temporaryOutput87[context->loop_idx].th31_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th32_dcpn_number_amt = temporaryOutput87[context->loop_idx].th32_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th33_dcpn_number_amt = temporaryOutput87[context->loop_idx].th33_dcpn_number_amt;

            //백동열 추가 20190213
            OUTPUT->grid01[context->tot_cnt].th34_dcpn_number_amt = temporaryOutput87[context->loop_idx].th34_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th36_dcpn_number_amt = temporaryOutput87[context->loop_idx].th36_dcpn_number_amt;

            //백동열 추가 20190304
            OUTPUT->grid01[context->tot_cnt].th37_dcpn_number_amt = temporaryOutput87[context->loop_idx].th37_dcpn_number_amt;

            //백동열 추가 20190425
            OUTPUT->grid01[context->tot_cnt].th38_dcpn_number_amt = temporaryOutput87[context->loop_idx].th38_dcpn_number_amt;

            // - 2016.09.10 : 지별괴장청
            OUTPUT->grid01[context->tot_cnt].th39_dcpn_number_amt = temporaryOutput87[context->loop_idx].th39_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th40_dcpn_number_amt = temporaryOutput87[context->loop_idx].th40_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th41_dcpn_number_amt = temporaryOutput87[context->loop_idx].th41_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th42_dcpn_number_amt = temporaryOutput87[context->loop_idx].th42_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th43_dcpn_number_amt = temporaryOutput87[context->loop_idx].th43_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th44_dcpn_number_amt = temporaryOutput87[context->loop_idx].th44_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th45_dcpn_number_amt = temporaryOutput87[context->loop_idx].th45_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th46_dcpn_number_amt = temporaryOutput87[context->loop_idx].th46_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th47_dcpn_number_amt = temporaryOutput87[context->loop_idx].th47_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th48_dcpn_number_amt = temporaryOutput87[context->loop_idx].th48_dcpn_number_amt;

            // 234925 장영철 20210119
            OUTPUT->grid01[context->tot_cnt].th49_dcpn_number_amt = temporaryOutput87[context->loop_idx].th49_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th50_dcpn_number_amt = temporaryOutput87[context->loop_idx].th50_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th51_dcpn_number_amt = temporaryOutput87[context->loop_idx].th51_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th52_dcpn_number_amt = temporaryOutput87[context->loop_idx].th52_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th53_dcpn_number_amt = temporaryOutput87[context->loop_idx].th53_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th54_dcpn_number_amt = temporaryOutput87[context->loop_idx].th54_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th55_dcpn_number_amt = temporaryOutput87[context->loop_idx].th55_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th56_dcpn_number_amt = temporaryOutput87[context->loop_idx].th56_dcpn_number_amt;

            // 243986 유준모 20220217
            OUTPUT->grid01[context->tot_cnt].th57_dcpn_number_amt = temporaryOutput87[context->loop_idx].th57_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th58_dcpn_number_amt = temporaryOutput87[context->loop_idx].th58_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th59_dcpn_number_amt = temporaryOutput87[context->loop_idx].th59_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th60_dcpn_number_amt = temporaryOutput87[context->loop_idx].th60_dcpn_number_amt;

            // 255042 최정훈 20230327
            OUTPUT->grid01[context->tot_cnt].th61_dcpn_number_amt = temporaryOutput87[context->loop_idx].th61_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th62_dcpn_number_amt = temporaryOutput87[context->loop_idx].th62_dcpn_number_amt;

            // 260793 박준기 20231017
            OUTPUT->grid01[context->tot_cnt].th8_ntgr_amt = temporaryOutput87[context->loop_idx].th8_ntgr_amt;
            OUTPUT->grid01[context->tot_cnt].th9_ntgr_amt = temporaryOutput87[context->loop_idx].th9_ntgr_amt;
            OUTPUT->grid01[context->tot_cnt].th63_dcpn_number_amt = temporaryOutput87[context->loop_idx].th63_dcpn_number_amt;

            // 270225 최정훈 20240502
            OUTPUT->grid01[context->tot_cnt].th64_dcpn_number_amt = temporaryOutput87[context->loop_idx].th64_dcpn_number_amt;

            // 272756 최정훈 20240627
            OUTPUT->grid01[context->tot_cnt].th65_dcpn_number_amt = temporaryOutput87[context->loop_idx].th65_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th66_dcpn_number_amt = temporaryOutput87[context->loop_idx].th66_dcpn_number_amt;
            OUTPUT->grid01[context->tot_cnt].th67_dcpn_number_amt = temporaryOutput87[context->loop_idx].th67_dcpn_number_amt;

            // 293062 유준모 20250811
            OUTPUT->grid01[context->tot_cnt].th68_dcpn_number_amt = temporaryOutput87[context->loop_idx].th68_dcpn_number_amt;

            // 항목추가
            // - 지별괴장청
            STRCPY( OUTPUT->grid01[context->tot_cnt].th7_ntgr_amt , temporaryOutput87[context->loop_idx].th7_ntgr_amt );
            OUTPUT->grid01[context->tot_cnt].th7_ntgr_amt = temporaryOutput87[context->loop_idx].th7_ntgr_amt;

            // 2016.09.10 지별괴장청
            OUTPUT->grid01[context->tot_cnt].th20_ltrs_cntn = temporaryOutput87[context->loop_idx].th20_ltrs_cntn;
            OUTPUT->grid01[context->tot_cnt].th7_ntgr_amt = temporaryOutput87[context->loop_idx].th7_ntgr_amt;

            OUTPUT->grid_cnt01++;

            if(context->tot_cnt >= AS_SRLGR96602A_OUT_GRID01)
            {
                PFM_DBG( "조회 건수가 Array Size 보다 클니다, 확인해 주세요. Array size [%ld]", context->tot_cnt);
                context->loop_status = FALSE;
                break;
            }
        }
        //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID26------------

        }
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:FETCH_LOOP_POST NODEID87------------
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:FETCH_LOOP_POST NODEID87--------------
    //END - while

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:FETCH_LOOP_POST NODEID87------------
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:FETCH_LOOP_POST NODEID87--------------
    //END_OF_CODE:PSTP_펀드_정보_이력_배치생성_다건조회Fetch Loop DBIO_FETCH_LOOP

    PFM_TRY(pfmDbioCloseCursorArray("RPT_RLGR_TM_VF701"));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_FETCH_LOOP_CLOSE_EXCEPTION NODEID87
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_FETCH_LOOP_CLOSE_EXCEPTION NODEID87--

    }
    }
    }
    {
    /*****************************************
     * KIND    : Virtual Module
     * NODE ID : 9
     * NAME    : 정상처리
     * DESCRIPTION :
     *
     *****************************************/
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID9----------------
    // TODO Auto-generated method stub
    if ( (INPUT->data_evnt_proc_hndl == DATA_PROC_SEL) ) {
        PFM_SET_MSG(  "ZCOM00006"
                   );
    }
    else{
        /* ZCOM00021 정상적으로 처리되었습니다.  */
        PFM_SET_MSG(  "ZCOM00021" );
        /* 출력 타입 1:Popup 2:MsgBox 3:Statebar
         * 4:멀티MsgBox 확인버튼               (입력전검증)
         * 5:멀티MsgBox 예/아니오               (입력전검증)
         * 6:멀티MsgBox 예/아니오/취소          (입력전검증)
         * 7:멀티MsgBox 확인버튼                (입력후검증)
         * 8:멀티MsgBox 예/아니오               (입력후검증)
         * 9:멀티MsgBox 예/아니오/취소(입력후검증)
         * 둘째자리수 : 알림속성  0:N/A  1:도착알림 음성출력 Ex) PFM_MSG(10) */
        PFM_MSGQ(10);
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID9------------------

    }
    return RC_NRM;

PFM_CATCH:
    return rc;
}
/*****************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 4
 * NAME    : 정상종료
 * DESCRIPTION :
 *
 *****************************************/
static long norm_exit_proc(SRLGR96602AContext *context)
{
    long rc = RC_NRM;
    // User Variables Declaration
    {
    /*****************************************
     * KIND    : Virtual Module
     * NODE ID : 9
     * NAME    : 정상처리
     * DESCRIPTION :
     *
     *****************************************/
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID9----------------
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID9------------------

    }
    return RC_NRM;

PFM_CATCH:
    return rc;
}
