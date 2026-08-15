/*
 * @file        SPCSP53619C.c
 * @filetype    c source file
 * @brief       DS_월간보고서_보고서탭_
 * @author      220113
 * @version
 * @dep-header
 * @history
 *      Version:    Name :  Date :      Reference :        Desciption :
 *      --------    ------  --------    -----------        ----------------------------------
 *      VER1.00 : 220113 : 20260226 : proframe 구축     : 신규 개발
 *
 */
/*****************************************
 * KIND    : Service Module Interface
 * NODE ID : 0
 * NAME    : DS_월간보고서_보고서탭_
 * DESCRIPTION :
 *   SPCSP53619C
 *****************************************/
#include "SPCSP53619C.h"
static MapperMapInfo mappingInfo = {PMAP_FLAG_TRACE_ON, 0, "", "", "", ""};
#if defined (__cplusplus)
    extern "C"
#endif
long SPCSP53619C(SPCSP53619C_IN *input, SPCSP53619C_OUT *output)
{
    SPCSP53619CContext  __context;
    SPCSP53619CContext *context = &__context;
    long rc = RC_NRM;
    bzero(context, sizeof(SPCSP53619CContext));
    context->input  = input;
    context->output = output;
    {
    /*****************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 108
     * NAME    : 초기화
     * DESCRIPTION :
     *
     *****************************************/
    PFM_TRY(init_proc(context));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:INNER_MODULE_EXCEPTION NODEID108-----------
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:INNER_MODULE_EXCEPTION NODEID108-------------

    }
    {
    /*****************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 1
     * NAME    : 입력검증
     * DESCRIPTION :
     *
     *****************************************/
    PFM_TRY(input_valid_proc(context));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:INNER_MODULE_EXCEPTION NODEID1-------------
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:INNER_MODULE_EXCEPTION NODEID1---------------

    }
    {
    /*****************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 2
     * NAME    : 본처리
     * DESCRIPTION :
     *
     *****************************************/
    PFM_TRY(main_proc(context));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:INNER_MODULE_EXCEPTION NODEID2-------------
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:INNER_MODULE_EXCEPTION NODEID2---------------

    }
    {
    /*****************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 3
     * NAME    : 정상종료
     * DESCRIPTION :
     *
     *****************************************/
    PFM_TRY(norm_exit_proc(context));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:INNER_MODULE_EXCEPTION NODEID3-------------
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:INNER_MODULE_EXCEPTION NODEID3---------------

    }
    return RC_NRM;

PFM_CATCH:
    {
    /*****************************************
     * KIND    : Virtual Module
     * NODE ID : 4
     * NAME    : 예외처리
     * DESCRIPTION :
     *
     *****************************************/
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID4------------------/
    // TODO Auto-generated method stub
    PFM_DBG("예외 처리 발생");
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID4------------------//

    }
    return rc;
}
/*****************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 108
 * NAME    : 초기화
 * DESCRIPTION :
 *
 *****************************************/
static long init_proc(SPCSP53619CContext *context)
{
    long rc = RC_NRM;
    // User Variables Declaration
    {
    /*****************************************
     * KIND    : Virtual Module
     * NODE ID : 109
     * NAME    : 초기화
     * DESCRIPTION :
     *
     *****************************************/
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID109-----------------
    // TODO Auto-generated method stub
    STRCPY( context->orig_trns_unq_id  , SysHdrInfo_GetOrig_trns_unq_id() ); /* 출처거래고유ID   */
    STRCPY( context->prgm_id           , SysHdrInfo_GetSrvc_code()        ); /* 프로그램ID       */
    STRCPY( context->user_id           , SysHdrInfo_GetUser_id()          ); /* 사용자ID         */
    STRCPY( context->lngg_dtcd         , SysHdrInfo_GetLngg_type()        ); /* 언어타입 2       */
    STRCPY( context->ls_ptrn_data_pacd , "53619M_1"                       );
    STRCPY( context->ls_ptrn_data_pacd2, "53619C"                         );

    rc = pfmNumGetFromLong (&context->num_999, 999);
    if(rc != RC_NRM) {
        PFM_ERR("%s", pfmNumGetErrorMsg());   /* 또는 PFM_ERR("%s", pfmUtilGetErrorMsg()); */
        PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류 발생.
        return RC_ERR;
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID109-----------------/.

    }
    {
    /*****************************************
     * KIND    : Module Call
     * NODE ID : 15
     * NAME    : 영업일조회
     * DESCRIPTION :
     *
     *****************************************/
    MPCOM_GetBzopDate_IN  temporaryInput;
    MPCOM_GetBzopDate_OUT temporaryOutput;
    bzero(&temporaryInput,  sizeof(MPCOM_GetBzopDate_IN));
    bzero(&temporaryOutput, sizeof(MPCOM_GetBzopDate_OUT));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID15-----------------
    // TODO Auto-generated method stub
    STRCPY(temporaryInput.thdy_incs_yn  ,  "N"               );
    STRCPY(temporaryInput.ntrd_incs_yn  ,  "N"               );
    STRCPY(temporaryInput.prsn_date     ,  INPUT->proc_date  );
    temporaryInput.calc_dycn            =  -1                ;
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID15-------------------

    /*****************************************
     * KIND    : Module Callee Info
     * NAME    : 영업일조회
     * INPUT   : MPCOM_GetBzopDate_IN
     * OUTPUT  : MPCOM_GetBzopDate_OUT
     *****************************************/
    PFM_TRYNJ(pfmDlCall("MPCOM_GetBzopDate", "MPCOM_GetBzopDate", &temporaryInput, &temporaryOutput));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:MODULE_EXCEPTION NODEID15-------------
    if(rc != RC_NRM)
    {
        /* 모듈 오류 */
        PFM_ERR("영업일조회 [%s]", pfmNumGetErrorMsg()); /* 또는 PFM_ERR("%s", pfmUtilGetErrorMsg()); */
        /* [%s] 호출 중 오류가 발생하였습니다. [오류내용=%s] */
        PFM_SET_ERR( "ZCOM00220"
                   , "MPCOM_GetBzopDate"
                   , "영업일조회 호출 오류"
                   );
        return RC_ERR;
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:MODULE_EXCEPTION NODEID15---------------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:AFTER_CODE NODEID15-------------------
    // TODO Auto-generated method stub
    STRCPY(context->ls_bzop_date, temporaryOutput.bzop_date);
    PRINT_MPCOM_GetBzopDate_OUT(&temporaryOutput);
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:AFTER_CODE NODEID15---------------------

    }
    return RC_NRM;

PFM_CATCH:
    return rc;
}
/*****************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 1
 * NAME    : 입력검증
 * DESCRIPTION :
 *
 *****************************************/
static long input_valid_proc(SPCSP53619CContext *context)
{
    long rc = RC_NRM;
    // User Variables Declaration
    {
    /*****************************************
     * KIND    : Virtual Module
     * NODE ID : 5
     * NAME    : 입력값 검증
     * DESCRIPTION :
     *
     *****************************************/
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID5------------------/.
    // TODO Auto-generated method stub
    NOT_NULL_PRINT_SPCSP53619C_IN(INPUT);
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID5------------------//

    }
    return RC_NRM;

PFM_CATCH:
    return rc;
}
/*****************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 2
 * NAME    : 본처리
 * DESCRIPTION :
 *
 *****************************************/
static long main_proc(SPCSP53619CContext *context)
{
    long rc = RC_NRM;
    // User Variables Declaration
    {
    /*****************************************
     * KIND    : Intermediary Module Block
     * NODE ID : 6
     * NAME    : 보고서 데이터 생성
     * DESCRIPTION :
     *
     *****************************************/
    // Variables Declaration
    char nd2_chec_yn[1 + 1];
    char st1_chec_yn[1 + 1];
    char ls_fund_code[6 + 1];
    // User Variables Declaration
    // Variables Initialization
    bzero(nd2_chec_yn, sizeof(nd2_chec_yn));
    bzero(st1_chec_yn, sizeof(st1_chec_yn));
    bzero(ls_fund_code, sizeof(ls_fund_code));
    {
    /*****************************************
     * KIND    : Intermediary Module Block
     * NODE ID : 8
     * NAME    : 펀드개요
     * DESCRIPTION :
     *
     *****************************************/
    // User Variables Declaration
    {
    /*****************************************
     * KIND    : DBIO Call
     * NODE ID : 17
     * NAME    : DS_월간보고서_펀드개요_단건조회
     * DESCRIPTION :
     *
     *****************************************/
    PFO_FUND_OVRV_PDAY_BS_DS101In  temporaryInput;
    PFO_FUND_OVRV_PDAY_BS_DS101Out temporaryOutput;
    PFO_FUND_OVRV_PDAY_BS_DS101Dyn pfmDbioClause;
    bzero(&pfmDbioClause,  sizeof(PFO_FUND_OVRV_PDAY_BS_DS101Dyn));
    bzero(&temporaryInput, sizeof(PFO_FUND_OVRV_PDAY_BS_DS101In));
    bzero(&temporaryOutput,sizeof(PFO_FUND_OVRV_PDAY_BS_DS101Out));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID17--------
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID17----------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID17-------------------
    // TODO Auto-generated method stub
    STRCPY(temporaryInput.mncm_code      , INPUT->mncm_code           );
    STRCPY(temporaryInput.fund_code      , INPUT->fund_code           );
    STRCPY(temporaryInput.ptrn_data_pacd , context->ls_ptrn_data_pacd );
    STRCPY(temporaryInput.proc_date      , INPUT->proc_date           );
    STRCPY(temporaryInput.aply_date      , INPUT->aply_date           );

    PRINT_PFO_FUND_OVRV_PDAY_BS_DS101In(&temporaryInput);

    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID17---------------------

    /*****************************************
     * KIND              : DBIO Callee Info
     * NAME              : DS_월간보고서_펀드개요_단건조회
     * EXEC              : SELECT
     * INPUT             : PFO_FUND_OVRV_PDAY_BS_DS101In
     * OUTPUT            : PFO_FUND_OVRV_PDAY_BS_DS101Out
     * ARRAY INPUT       : NONE
     * ARRAY OUTPUT      : NONE
     * DYNAMIC STRUCTURE : PFO_FUND_OVRV_PDAY_BS_DS101Dyn
     *****************************************/
    PFM_TRYNJ(pfmDbioSelect("PFO_FUND_OVRV_PDAY_BS_DS101", &temporaryInput, &temporaryOutput, &pfmDbioClause, PFMDBIO_NOLOCK));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_EXCEPTION NODEID17-----------------

    if( rc != RC_NRM) /* DBIO 예외처리 */
    {
        if( rc == RC_NFD)
        {
            PFM_ERR("[FAIL] DBIO : select data not found!!! "); /* 조회조건에 맞는 값이 없음 */
            /* RC_NFD 시의 업무에 따른 알맞은 메시지 처리(에러, 정상 처리결정) */
            /* ZCOM00003 : 해당 조건의 데이터가 없습니다. */
            PFM_SET_MSG("ZCOM00003"); // 맞는 유형의 메시지 코드 설정
            return RC_NRM; /* select시 RC_NFD는 default로 RC_NRM을 리턴(업무에 따라 변경가능) */
        }
        else
        {
            /* DBIO 오류 */
            PFM_ERR("[FAIL] DBIO : error [%ld][%s]", PDB_ERRORNUM, PDB_ERRORSTR);
            /* ZCOM00005 : 조회처리 중 오류가 발생하였습니다.[DB오류코드:%ld]. 시스템담당자에게 문의하세요. */
            PFM_SET_ERR("ZCOM00005", PDB_ERRORNUM);
            return RC_ERR;
        }
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_EXCEPTION NODEID17-------------------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:AFTER_CODE NODEID17---------------------
    // TODO Auto-generated method stub
    STRCPY(OUTPUT->fund_name              , temporaryOutput.fund_name              );
    STRCPY(OUTPUT->st1_infr_ltrs_cntn     , temporaryOutput.st1_infr_ltrs_cntn     );
    STRCPY(OUTPUT->nd2_infr_ltrs_cntn     , temporaryOutput.nd2_infr_ltrs_cntn     );
    STRCPY(OUTPUT->fund_type_dncd         , temporaryOutput.fund_type_dncd         );
    STRCPY(OUTPUT->st1_fund_ovrv_cntn     , temporaryOutput.st1_fund_ovrv_cntn     );
    STRCPY(OUTPUT->nd2_fund_ovrv_cntn     , temporaryOutput.nd2_fund_ovrv_cntn     );
    STRCPY(OUTPUT->th3_fund_ovrv_cntn     , temporaryOutput.th3_fund_ovrv_cntn     );
    STRCPY(OUTPUT->th4_fund_ovrv_cntn     , temporaryOutput.th4_fund_ovrv_cntn     );
    STRCPY(OUTPUT->th5_fund_ovrv_cntn     , temporaryOutput.th5_fund_ovrv_cntn     );
    STRCPY(OUTPUT->th6_fund_ovrv_cntn     , temporaryOutput.th6_fund_ovrv_cntn     );

    STRCPY(OUTPUT->st1_rprt_cntn          , temporaryOutput.st1_rprt_cntn          );
    STRCPY(OUTPUT->th3_infr_ltrs_cntn     , temporaryOutput.th3_infr_ltrs_cntn     );
    STRCPY(OUTPUT->th4_infr_ltrs_cntn     , temporaryOutput.th4_infr_ltrs_cntn     );
    STRCPY(OUTPUT->th5_infr_ltrs_cntn     , temporaryOutput.th5_infr_ltrs_cntn     );
    STRCPY(OUTPUT->th6_infr_ltrs_cntn     , temporaryOutput.th6_infr_ltrs_cntn     );

    OUTPUT->stup_amt                      = temporaryOutput.stup_amt               ;
    OUTPUT->fund_rnrt                     = temporaryOutput.fund_rnrt              ;

    STRCPY(st1_chec_yn, temporaryOutput.st1_chec_yn); // 클래스펀드 출력여부 ( 운용실적란에서... )
    STRCPY(nd2_chec_yn, temporaryOutput.nd2_chec_yn); // BM 출력여부 ( 운용실적란에서... )
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:AFTER_CODE NODEID17-----------------------

    }

    }
    {
    /*****************************************
     * KIND    : Intermediary Module Block
     * NODE ID : 9
     * NAME    : 운용실적
     * DESCRIPTION :
     *
     *****************************************/
    // Variables Declaration
    char ls_key[50 + 1];
    long ix = 0;                    /* for loop index */
    long tot_cnt = 0;                /* fetch total count */
    long cur_cnt = 0;                /* fetch current count */
    long loop_status = 0;            /* loop exit flag */
    char w_gijun_ymd[8 + 1];
    PfmNumber w_calc = PFMNUM_ZERO;
    PfmNumber arr_suik_rt[10];
    long w_nday = 0;
    long w_cnt = 0;
    // User Variables Declaration
    // Variables Initialization
    bzero(ls_key, sizeof(ls_key));
    bzero(w_gijun_ymd, sizeof(w_gijun_ymd));
    bzero(arr_suik_rt, sizeof(arr_suik_rt));
    {
    /*****************************************
     * KIND    : DBIO Fetch Loop
     * NODE ID : 36
     * NAME    : 운용펀드_종류형펀드_BM_목록 다건조회Fetch Loop
     * DESCRIPTION :
     *
     *****************************************/
    PFO_FUND_BS_DF036Dyn pfmDbioClause;
    bzero(&pfmDbioClause, sizeof(PFO_FUND_BS_DF036Dyn));
    PFO_FUND_BS_DF036In  temporaryInput36;
    PFO_FUND_BS_DF036Out temporaryOutput36[50];
    bzero(&temporaryInput36, sizeof(PFO_FUND_BS_DF036In));
    bzero(temporaryOutput36, sizeof(PFO_FUND_BS_DF036Out) * 50);
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID37--------
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER NODEID37----------

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID37-------------------
    // TODO Auto-generated method stub
    STRCPY(ls_key, "PCSP53619P02");
    STRCAT(ls_key, INPUT->aply_date);


    /* 입력값 셋팅 */
    STRCPY(temporaryInput36.mncm_code      , INPUT->mncm_code ); // 운용사코드
    STRCPY(temporaryInput36.fund_code      , INPUT->fund_code ); // 펀드코드
    STRCPY(temporaryInput36.mncm_date_gpcd , ls_key           ); // 패턴데이터구분코드
    /* DBIO구조체 debug로그 print */
    PRINT_PFO_FUND_BS_DF036In(&temporaryInput36);
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID37---------------------

    PFM_TRYNJ(pfmDbioOpenCursorArray("PFO_FUND_BS_DF036", &temporaryInput36, &pfmDbioClause));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_FETCH_LOOP_OPEN_EXCEPTION NODEID36---
    if(PDB_CHK_FAIL) {
        PFM_ERR("Cursor open error DBIO[%s], ERR_NO[%ld], ERR_STR[%s]", "운용펀드_종류형펀드_BM_목록 다건조회", PDB_ERRORNUM, PDB_ERRORSTR);
        return rc;
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_FETCH_LOOP_OPEN_EXCEPTION NODEID36-----

    //START_OF_CODE:운용펀드_종류형펀드_BM_목록 다건조회Fetch Loop DBIO_FETCH_LOOP
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:FETCH_LOOP_PRE NODEID36-----------------
    loop_status = TRUE;    /* loop탈출변수 초기화 */
    tot_cnt = cur_cnt = 0;  /* 건수 초기화 */
    while (loop_status)
    {
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:FETCH_LOOP_PRE NODEID36-------------------
        {
        /*****************************************
         * KIND              : DBIO_FETCH Callee Info
         * NAME              : 운용펀드_종류형펀드_BM_목록 다건조회
         * EXEC              : FETCH
         * INPUT             : PFO_FUND_BS_DF036In
         * OUTPUT            : PFO_FUND_BS_DF036Out
         * ARRAY INPUT       : NONE
         * ARRAY OUTPUT      : PFO_FUND_BS_DF036BundleOut
         * DYNAMIC STRUCTURE : PFO_FUND_BS_DF036Dyn
         *****************************************/
        PFM_TRYNJ(pfmDbioFetchCursorArray("PFO_FUND_BS_DF036", 50, &temporaryOutput36, &pfmDbioClause));
        //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_FETCH_EXCEPTION NODEID36--------
        if(rc != RC_NRM)
        {
            if(rc == RC_NFD)
            {
                if(PDB_RECNUM == 0)
                {
                    /* 업무에 맞게 판단!!! 여기서는 데이터가 한건도 없는경우 오류 처리하는것으로 함 */
                    /* CASE 1 : 오류처리 */
                    //PFM_ERR("[FAIL] DBIO : Fetch data not found!!! "); /* 조회조건에 맞는 값이 없음 */
                    /* ZCOM00003 : 해당 조건의 데이터가 없습니다. */
                    //PFM_SET_ERR("ZCOM00003"); // 맞는 유형의 메시지 코드 셋팅
                    //pfmDbioCloseCursorArray("OK_IMSI_META_VF001"); /* Cursor close */
                    //return RC_ERR; /* select시 RC_NFD default로 RC_NRM을 리턴(업무에 따라 변경가능) */

                    /* CASE 2 : 정상처리 */
                    PFM_DBG("[FAIL] DBIO : Fetch data not found!!! ");
                    /* 조회조건에 맞는 값이 없음 */ /* RC_NFD 시의 업무에 따른 알맞은 메시지 처리(에러, 정상 처리결정) */
                    /* RC_NFD 시의 업무에 따른 알맞은 메시지 처리(에러, 정상 처리결정) */
                    /* ZCOM00003 : 해당 조건의 데이터가 없습니다. */
                    PFM_SET_MSG("ZCOM00003"); /* 맞는 유형의 메시지 코드 셋팅 */
                    /* ZCOM00145 : 데이터 조회 중 오류발생. [%s], [%ld][%s] */
                    PFM_SET_ADD_ERR( "ZCOM00145"
                                    , "PFO_FUND_BS_DF036"
                                    , PDB_ERRORNUM
                                    , PDB_ERRORSTR
                                    );
                    PFM_MSGQ(30); /* 첫자리 3- Statebar,  둘째자리: 0-무음 */
                    pfmDbioCloseCursorArray("PFO_FUND_BS_DF036"); /* Cursor close */
                    return RC_NRM; /* select시 RC_NFD는 default로 RC_NRM을 리턴(업무에 따라 변경가능) */

                }

                /* 한번에 Fetch 한 건수가 Fetch Array Size 보다 작을 경우는 Not Found 아님(마지막 페이지) */
                loop_status = FALSE;
            }
            else
            {
                /* DBIO 오류 */
                PFM_ERR("[FAIL] DBIO : error [%ld][%s]", PDB_ERRORNUM, PDB_ERRORSTR);
                /* ZCOM00005 : 조회처리 중 오류가 발생하였습니다.[DB오류코드:%ld]. 시스템담당자에게 문의하세요. */
                PFM_SET_ERR( "ZCOM00005"
                           , PDB_ERRORNUM
                           ); /* 맞는 유형의 메시지 코드 셋팅 */
                /* ZCOM00145 : 데이터 조회 중 오류발생. [%s], [%ld][%s] */
                PFM_SET_ADD_ERR( "ZCOM00145"
                                , "PFO_FUND_BS_DF036"
                                , PDB_ERRORNUM
                                , PDB_ERRORSTR
                                );
                PFM_SET_ERR_ATTR(20); /* 첫자리 2- 메시지박스,  둘째자리: 0-무음 */
                pfmDbioCloseCursorArray("PFO_FUND_BS_DF036"); /* Cursor close */
                return RC_ERR;
            }
        }

        cur_cnt = PDB_RECNUM - tot_cnt; /* 현재 Fetch 건수 */
        tot_cnt = PDB_RECNUM;           /* 누적 Fetch 건수 */

        PFM_DBG("패치로직 데이터 건수 확인");
        PFM_DBG("DBIO FETCH : cur_cnt [%ld]", cur_cnt);
        PFM_DBG("DBIO FETCH : tot_cnt [%ld]", tot_cnt);
        //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_FETCH_EXCEPTION NODEID36----------

        //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:AFTER_CODE NODEID37------------------
        // TODO Auto-generated method stub
        //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:AFTER_CODE NODEID37--------------------

        }
        {
        /*****************************************
         * KIND    : Loop Module
         * NODE ID : 38
         * NAME    : 출력 루프
         * DESCRIPTION :
         *
         *****************************************/
        //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:LOOP_MODULE_PRE NODEID38------------
        for(ix = 0; ix < cur_cnt; ix++)
        {
        //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:LOOP_MODULE_PRE NODEID38--------------
            if(
            //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE_CONDITION NODEID26--
                STRCMP(temporaryOutput36[ix].trgt_dtcd, "2") == 0
            //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE_CONDITION NODEID26----
            )
            {
            /*****************************************
             * KIND    : Virtual Module
             * NODE ID : 26
             * NAME    : 클래스펀드         출력여부 체크
             * DESCRIPTION :
             *
             *****************************************/
            //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID26----------
            // TODO Auto-generated method stub
            // 0 : 출력안함,  1 : 출력함
            if ( STRCMP(st1_chec_yn, "0") == 0 || STRCMP(st1_chec_yn, "") == 0 ){
                continue;
            }
            //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID26------------

            }
            if(
            //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE_CONDITION NODEID29--
                STRCMP(temporaryOutput36[ix].trgt_dtcd, "3") == 0
            //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE_CONDITION NODEID29----
            )
            {
            /*****************************************
             * KIND    : Virtual Module
             * NODE ID : 29
             * NAME    : BM         출력여부 체크
             * DESCRIPTION :
             *
             *****************************************/
            //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID29----------
            // TODO Auto-generated method stub
            // 0 : 출력안함,  1 : 출력함
            if ( STRCMP(nd2_chec_yn, "0") == 0  || STRCMP(nd2_chec_yn, "") == 0 ){
                continue;
            }
            //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID29------------

            }
            {
            /*****************************************
             * KIND    : Virtual Module
             * NODE ID : 39
             * NAME    : 출력 체크
             * DESCRIPTION :
             *
             *****************************************/
            //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID39----------
            // TODO Auto-generated method stub
            if(OUTPUT->grid_cnt03 >= AS_SPCSP53619C_OUT_GRID03)
            {
                PFM_DBG("출력값 Array 범위초과");
                PFM_DBG("OUTPUT_DATA :: Grid Array Size OverFlow!!!");
                loop_status = FALSE;
                break;
            }
            //bzero(arr_suik_rt, sizeof(arr_suik_rt));
            arr_suik_rt[0] = PFMNUM_ZERO;
            arr_suik_rt[1] = PFMNUM_ZERO;
            arr_suik_rt[2] = PFMNUM_ZERO;
            arr_suik_rt[3] = PFMNUM_ZERO;
            arr_suik_rt[4] = PFMNUM_ZERO;
            arr_suik_rt[5] = PFMNUM_ZERO;
            //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID39------------

            }
            {
            /*****************************************
             * KIND    : Loop Module
             * NODE ID : 40
             * NAME    : 기간수익률 루프
             * DESCRIPTION :
             *
             *****************************************/
            //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:LOOP_MODULE_PRE NODEID40--------
            for(w_cnt = 1; w_cnt <= 8; w_cnt++)
            {
            //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:LOOP_MODULE_PRE NODEID40----------
                {
                /*****************************************
                 * KIND    : Virtual Module
                 * NODE ID : 42
                 * NAME    : 일자설정
                 * DESCRIPTION :
                 *
                 *****************************************/
                //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID42------
                // TODO Auto-generated method stub
                if(w_cnt == 1)
                { // 1개월
                    rc = zpfmAddMonthOra(INPUT->proc_date, -1, w_gijun_ymd); //기준일자
                    if (rc != RC_NRM) {
                        PFM_ERR("zpfmAddMonthOra : 월더하기 오류입니다.  : %s  rc : [%ld]", pfmNumGetErrorMsg(), rc);
                        PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류 발생.
                        return RC_ERR;
                    }
                    /* 한편(PFM_CALC_ONE)/양편(PFM_CALC_BOTH), 입력일자, 일수(가감)를 전달받아 */
                    rc = zpfmAddDate(PFM_CALC_ONE, w_gijun_ymd, 1, w_gijun_ymd); /* YYYYMMDD */
                    if (rc != RC_NRM) {
                        PFM_ERR("zpfmAddDate : 일더하기 오류입니다.");
                        PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류 발생.
                        return RC_ERR;
                    }
                }
                else if(w_cnt == 2)
                { // 3개월
                    rc = zpfmAddMonthOra(INPUT->proc_date, -3, w_gijun_ymd); //기준일자
                    if (rc != RC_NRM) {
                        PFM_ERR("zpfmAddMonthOra : 월더하기 오류입니다.  : %s  rc : [%ld]", pfmNumGetErrorMsg(), rc);
                        PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류 발생.
                        return RC_ERR;
                    }
                    /* 한편(PFM_CALC_ONE)/양편(PFM_CALC_BOTH), 입력일자, 일수(가감)를 전달받아 */
                    rc = zpfmAddDate(PFM_CALC_ONE, w_gijun_ymd, 1, w_gijun_ymd); /* YYYYMMDD */
                    if (rc != RC_NRM) {
                        PFM_ERR("zpfmAddDate : 일더하기 오류입니다.");
                        PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류 발생.
                        return RC_ERR;
                    }
                }
                else if(w_cnt == 3)
                { // 6개월
                    rc = zpfmAddMonthOra(INPUT->proc_date, -6, w_gijun_ymd); //기준일자
                    if (rc != RC_NRM) {
                        PFM_ERR("zpfmAddMonthOra : 월더하기 오류입니다.  : %s  rc : [%ld]", pfmNumGetErrorMsg(), rc);
                        PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류 발생.
                        return RC_ERR;
                    }
                    /* 한편(PFM_CALC_ONE)/양편(PFM_CALC_BOTH), 입력일자, 일수(가감)를 전달받아 */
                    rc = zpfmAddDate(PFM_CALC_ONE, w_gijun_ymd, 1, w_gijun_ymd); /* YYYYMMDD */
                    if (rc != RC_NRM) {
                        PFM_ERR("zpfmAddDate : 일더하기 오류입니다.");
                        PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류 발생.
                        return RC_ERR;
                    }
                }
                else if(w_cnt == 4)
                { // 1년
                    rc = zpfmAddMonthOra(INPUT->proc_date, -12, w_gijun_ymd); //기준일자
                    if (rc != RC_NRM) {
                        PFM_ERR("zpfmAddMonthOra : 월더하기 오류입니다.  : %s  rc : [%ld]", pfmNumGetErrorMsg(), rc);
                        PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류 발생.
                        return RC_ERR;
                    }
                    /* 한편(PFM_CALC_ONE)/양편(PFM_CALC_BOTH), 입력일자, 일수(가감)를 전달받아 */
                    rc = zpfmAddDate(PFM_CALC_ONE, w_gijun_ymd, 1, w_gijun_ymd); /* YYYYMMDD */
                    if (rc != RC_NRM) {
                        PFM_ERR("zpfmAddDate : 일더하기 오류입니다.");
                        PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류 발생.
                        return RC_ERR;
                    }
                }
                else if(w_cnt == 5)
                { // 3년
                    rc = zpfmAddMonthOra(INPUT->proc_date, -36, w_gijun_ymd); //기준일자
                    if (rc != RC_NRM) {
                        PFM_ERR("zpfmAddMonthOra : 월더하기 오류입니다.  : %s  rc : [%ld]", pfmNumGetErrorMsg(), rc);
                        PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류 발생.
                        return RC_ERR;
                    }
                    /* 한편(PFM_CALC_ONE)/양편(PFM_CALC_BOTH), 입력일자, 일수(가감)를 전달받아 */
                    rc = zpfmAddDate(PFM_CALC_ONE, w_gijun_ymd, 1, w_gijun_ymd); /* YYYYMMDD */
                    if (rc != RC_NRM) {
                        PFM_ERR("zpfmAddDate : 일더하기 오류입니다.");
                        PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류 발생.
                        return RC_ERR;
                    }
                }
                else if(w_cnt == 6)
                { // 5년
                    rc = zpfmAddMonthOra(INPUT->proc_date, -60, w_gijun_ymd); //기준일자
                    if (rc != RC_NRM) {
                        PFM_ERR("zpfmAddMonthOra : 월더하기 오류입니다.  : %s  rc : [%ld]", pfmNumGetErrorMsg(), rc);
                        PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류 발생.
                        return RC_ERR;
                    }
                    /* 한편(PFM_CALC_ONE)/양편(PFM_CALC_BOTH), 입력일자, 일수(가감)를 전달받아 */
                    rc = zpfmAddDate(PFM_CALC_ONE, w_gijun_ymd, 1, w_gijun_ymd); /* YYYYMMDD */
                    if (rc != RC_NRM) {
                        PFM_ERR("zpfmAddDate : 일더하기 오류입니다.");
                        PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류 발생.
                        return RC_ERR;
                    }
                }
                else if(w_cnt == 7)
                { // 연초이후
                    char tmp_date[9] = "";
                    zpfmSubString(INPUT->proc_date, 0, 4, tmp_date);
                    STRCAT(tmp_date, "0101");
                    STRCPY(w_gijun_ymd, tmp_date);
                }
                else if(w_cnt == 8)
                { // 설정일자이후
                    STRCPY(w_gijun_ymd, temporaryOutput36[ix].firt_stup_date); //설정일자
                }
                //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID42--------

                }
                if(
                //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:MODULE_CONDITION NODEID44----
                    STRCMP(temporaryOutput36[ix].trgt_dtcd, "1") == 0 ||  // 1 : 운용펀드, 2 : 클래스펀드
                    STRCMP(temporaryOutput36[ix].trgt_dtcd, "2") == 0
                //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:MODULE_CONDITION NODEID44------
                )
                {
                /*****************************************
                 * KIND    : Module Call
                 * NODE ID : 43
                 * NAME    : 수익률 산출
                 * DESCRIPTION :
                 *   // TODO Auto-generated method stub
                 *
                 *****************************************/
                MPCOM_CalcFndRntn_IN  temporaryInput;
                MPCOM_CalcFndRntn_OUT temporaryOutput;
                bzero(&temporaryInput,  sizeof(MPCOM_CalcFndRntn_IN));
                bzero(&temporaryOutput, sizeof(MPCOM_CalcFndRntn_OUT));
                //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID43--------
                // TODO Auto-generated method stub
                w_calc = PFMNUM_ZERO;

                STRCPY(temporaryInput.lngg_dtcd        , SysHdrInfo_GetLngg_type()          );
                STRCPY(temporaryInput.mncm_code        , INPUT->mncm_code                   );
                STRCPY(temporaryInput.fund_code        , temporaryOutput36[ix].fund_code    );
                STRCPY(temporaryInput.rnrt_cmpu_mhcd   , "1"                                );
                STRCPY(temporaryInput.strn_date        , w_gijun_ymd                        );
                STRCPY(temporaryInput.end_date         , INPUT->proc_date                   );
                //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID43----------

                /*****************************************
                 * KIND    : Module Callee Info
                 * NAME    : 수익률 산출
                 * INPUT   : MPCOM_CalcFndRntn_IN
                 * OUTPUT  : MPCOM_CalcFndRntn_OUT
                 *****************************************/
                PFM_TRYNJ(pfmDlCall("MPCOM_CalcFndRntn", "MPCOM_CalcFndRntn", &temporaryInput, &temporaryOutput));
                //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:MODULE_EXCEPTION NODEID43----
                if(rc != RC_NRM)
                {
                    /* 모듈 오류 */
                    PFM_ERR("수익률 산출 [%s]", pfmNumGetErrorMsg());     /* 또는 PFM_ERR("%s", pfmUtilGetErrorMsg()); */
                    /* [%s] 호출 중 오류가 발생하였습니다. [오류내용=%s] */
                    PFM_SET_ERR( "ZCOM00220"
                               , "MPCOM_CalcFndRntn"
                               , "수익률 산출 호출 오류"
                               );
                    return RC_ERR;
                }
                //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:MODULE_EXCEPTION NODEID43------

                //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:AFTER_CODE NODEID43----------
                // TODO Auto-generated method stub
                /* 사칙연산 */
                rc = pfmNumCalc(&w_calc, "%n * 100", temporaryOutput.rnrt);
                /* long형 : %ld , 문자형 : %s, Number형 : %n  */
                if (rc != RC_NRM )
                {
                    PFM_ERR("pfmNumCalc : %s  rc : [%ld]", pfmNumGetErrorMsg(), rc)
                    PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류 발생.
                    return RC_ERR;
                }
                //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:AFTER_CODE NODEID43------------

                }
                else
                {
                /*****************************************
                 * KIND    : Module Call
                 * NODE ID : 45
                 * NAME    : BM 수익률 계산
                 * DESCRIPTION :
                 *
                 *****************************************/
                MPCOM_CalcBmRnrt_IN  temporaryInput;
                MPCOM_CalcBmRnrt_OUT temporaryOutput;
                bzero(&temporaryInput,  sizeof(MPCOM_CalcBmRnrt_IN));
                bzero(&temporaryOutput, sizeof(MPCOM_CalcBmRnrt_OUT));
                //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID45--------
                // TODO Auto-generated method stub
                w_calc = PFMNUM_ZERO;

                STRCPY(temporaryInput.lngg_dtcd        , SysHdrInfo_GetLngg_type()          );
                STRCPY(temporaryInput.mncm_code        , INPUT->mncm_code                   );
                STRCPY(temporaryInput.fund_code        , temporaryOutput36[ix].fund_code    );
                STRCPY(temporaryInput.dtcd             , "1"                                );
                STRCPY(temporaryInput.strn_date        , w_gijun_ymd                        );
                STRCPY(temporaryInput.end_date         , INPUT->proc_date                   );
                //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID45----------

                /*****************************************
                 * KIND    : Module Callee Info
                 * NAME    : BM 수익률 계산
                 * INPUT   : MPCOM_CalcBmRnrt_IN
                 * OUTPUT  : MPCOM_CalcBmRnrt_OUT
                 *****************************************/
                PFM_TRYNJ(pfmDlCall("MPCOM_CalcBmRnrt", "MPCOM_CalcBmRnrt", &temporaryInput, &temporaryOutput));
                //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:MODULE_EXCEPTION NODEID45----
                if(rc != RC_NRM)
                {
                    /* 모듈 오류 */
                    PFM_ERR("수익률 산출 [%s]", pfmNumGetErrorMsg());     /* 또는 PFM_ERR("%s", pfmUtilGetErrorMsg()); */
                    /* [%s] 호출 중 오류가 발생하였습니다. [오류내용=%s] */
                    PFM_SET_ERR( "ZCOM00220"
                               , "MPCOM_CalcBmRnrt"
                               , "BM 수익률 산출 호출 오류"
                               );
                    return RC_ERR;
                }
                //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:MODULE_EXCEPTION NODEID45------

                //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:AFTER_CODE NODEID45----------
                // TODO Auto-generated method stub
                //BM수익률
                /* 사칙연산 */
                rc = pfmNumCalc(&w_calc, "%n * 100", temporaryOutput.rnrt);
                /* long형 : %ld , 문자형 : %s, Number형 : %n  */
                if (rc != RC_NRM )
                {
                    PFM_ERR("pfmNumCalc : %s  rc : [%ld]", pfmNumGetErrorMsg(), rc)
                    PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류 발생.
                    return RC_ERR;
                }
                //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:AFTER_CODE NODEID45------------

                }
                {
                /*****************************************
                 * KIND    : Virtual Module
                 * NODE ID : 46
                 * NAME    : 수익률체크
                 * DESCRIPTION :
                 *
                 *****************************************/
                //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID46------
                // TODO Auto-generated method stub

                if(STRCMP(temporaryOutput36[ix].trgt_dtcd, "1") == 0)
                {
                    if(STRCMP(w_gijun_ymd , temporaryOutput36[ix].firt_stup_date) < 0)
                    {

                        arr_suik_rt[w_cnt] = context->num_999;
                    }
                    else
                    {
                        /* 반올림  */
                        rc = pfmNumRoundAt(&arr_suik_rt[w_cnt], w_calc, 2);
                        if (rc != RC_NRM ) {
                            PFM_ERR("pfmNumRoundAt : %s  rc : [%ld]", pfmNumGetErrorMsg(), rc);
                            PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류 발생.
                            return RC_ERR;
                        }
                    }
                }
                else
                {
                    if(STRCMP(w_gijun_ymd , temporaryOutput36[ix].firt_stup_date) < 0)
                    {
                        arr_suik_rt[w_cnt] = context->num_999;
                    }
                    else
                    {
                        /* 반올림  */
                        rc = pfmNumRoundAt(&arr_suik_rt[w_cnt], w_calc, 2);
                        if (rc != RC_NRM ) {
                            PFM_ERR("pfmNumRoundAt : %s  rc : [%ld]", pfmNumGetErrorMsg(), rc);
                            PFM_SET_ERR("SBND00007", __LINE__); // 체크 및 계산 처리 오류
                            return RC_ERR;
                        }
                    }
                }
                //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID46--------

                }
            //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:LOOP_MODULE_POST NODEID40--------
            } //end for(기간수익률)
            //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:LOOP_MODULE_POST NODEID40----------

            }
            {
            /*****************************************
             * KIND    : Virtual Module
             * NODE ID : 41
             * NAME    : SUB03
             * DESCRIPTION :
             *
             *****************************************/
            //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID41----------
            STRCPY(OUTPUT->grid03[OUTPUT->grid_cnt03].trgt_dtcd    , temporaryOutput36[ix].trgt_dtcd     );
            STRCPY(OUTPUT->grid03[OUTPUT->grid_cnt03].fund_code    , temporaryOutput36[ix].fund_code     );
            STRCPY(OUTPUT->grid03[OUTPUT->grid_cnt03].fund_name    , temporaryOutput36[ix].fund_name     );
            STRCPY(OUTPUT->grid03[OUTPUT->grid_cnt03].stup_date    , temporaryOutput36[ix].firt_stup_date);

            OUTPUT->grid03[OUTPUT->grid_cnt03].mn1_rnrt             = arr_suik_rt[1];
            OUTPUT->grid03[OUTPUT->grid_cnt03].mn3_rnrt             = arr_suik_rt[2];
            OUTPUT->grid03[OUTPUT->grid_cnt03].mn6_rnrt             = arr_suik_rt[3];
            OUTPUT->grid03[OUTPUT->grid_cnt03].yr1_rnrt             = arr_suik_rt[4];
            OUTPUT->grid03[OUTPUT->grid_cnt03].yr3_rnrt             = arr_suik_rt[5];
            OUTPUT->grid03[OUTPUT->grid_cnt03].yr5_rnrt             = arr_suik_rt[6];
            OUTPUT->grid03[OUTPUT->grid_cnt03].st1_rnrt             = arr_suik_rt[7];
            OUTPUT->grid03[OUTPUT->grid_cnt03].nd2_rnrt             = arr_suik_rt[8];

            /* 출력 건수 카운팅 */
            OUTPUT->grid_cnt03++;

            //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID41------------

            }
        //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:LOOP_MODULE_POST NODEID38-----------
        } //end for
        //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:LOOP_MODULE_POST NODEID38-------------

        }
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:FETCH_LOOP_POST NODEID36-------------
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:FETCH_LOOP_POST NODEID36---------------
    //END_OF_CODE:운용펀드_종류형펀드_BM_목록 다건조회Fetch Loop DBIO_FETCH_LOOP

    PFM_TRY(pfmDbioCloseCursorArray("PFO_FUND_BS_DF036"));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_FETCH_LOOP_CLOSE_EXCEPTION NODEID36-
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_FETCH_LOOP_CLOSE_EXCEPTION NODEID36---

    }

    }

    }
    return RC_NRM;

PFM_CATCH:
    return rc;
}
/*****************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 3
 * NAME    : 정상종료
 * DESCRIPTION :
 *
 *****************************************/
static long norm_exit_proc(SPCSP53619CContext *context)
{
    long rc = RC_NRM;
    // User Variables Declaration
    {
    /*****************************************
     * KIND    : Virtual Module
     * NODE ID : 7
     * NAME    : 정상처리
     * DESCRIPTION :
     *
     *****************************************/
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID7------------------/.
    // TODO Auto-generated method stub
    PFM_DBG("정상 종료");
    NOT_NULL_PRINT_SPCSP53619C_OUT(OUTPUT);
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID7------------------//

    }
    return RC_NRM;

PFM_CATCH:
    return rc;
}
