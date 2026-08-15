/*
 * @file        BRLGRPRP0001.c
 * @filetype    c source file
 * @brief       제안서_대상펀드리스트_배치
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
 * KIND    : Batch Module Interface
 * NODE ID : 0
 * NAME    : 제안서_대상펀드리스트_배치
 * DESCRIPTION :
 *   SRLGR96602A에서 온라인배치(MZPFM_BatchLinkCall)로 호출됨
 *****************************************/
#include "BRLGRPRP0001.h"

static MapperMapInfo mappingInfo = {PMAP_FLAG_TRACE_ON, 0, "", "", "", ""};

#if defined (__cplusplus)
    extern "C"
#endif

long BRLGRPRP0001(BRLGRPRP0001_IN *input, BRLGRPRP0001_OUT *output)
{
    BRLGRPRP0001Context  __context;
    BRLGRPRP0001Context *context = &__context;

    long rc = RC_NRM;

    bzero(context, sizeof(BRLGRPRP0001Context));
    context->input  = input;
    context->output = output;

    {
    /*****************************************
     * KIND    : Virtual Module
     * NODE ID : 1
     * NAME    : 초기화
     * DESCRIPTION :
     *
     *****************************************/
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID1-----------------
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID1-------------------

    }
    {
    /*****************************************
     * KIND    : DBIO Module Function Call
     * NODE ID : 10
     * NAME    : 펀드기본 조회
     * DESCRIPTION :
     *
     *****************************************/
    PFO_FUND_BS_DF037In  temporaryInput;
    PFO_FUND_BS_DF037Out temporaryOutput;
    bzero(&temporaryInput,  sizeof(PFO_FUND_BS_DF037In));
    bzero(&temporaryOutput, sizeof(PFO_FUND_BS_DF037Out));

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID10------------------
    /* 입력값 셋팅 */
    STRCPY(temporaryInput.mncm_code, context->btch_mncm_code);   // 운용사코드
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID10--------------------

    /*****************************************
     * KIND    : DBIO Callee Info
     * NAME    : 펀드기본 조회
     * EXEC    : SELECT
     * INPUT   : PFO_FUND_BS_DF037In
     * OUTPUT  : PFO_FUND_BS_DF037Out
     *****************************************/
    PFM_TRYNJ(pfmDbioOpenCursorArray("PFO_FUND_BS_DF037", &temporaryInput, &temporaryOutput, NULL, PFMDBIO_NOLOCK));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_EXCEPTION NODEID10------------------
    if( rc != RC_NRM)
    {
        PFM_SET_ERR("ZCOM00003", "PFO_FUND_BS_DF037");
        return RC_ERR;
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_EXCEPTION NODEID10--------------------

    }
    {
    /*****************************************
     * KIND    : DBIO Module Function Call
     * NODE ID : 20
     * NAME    : 주식 보유종목 상위조회
     * DESCRIPTION :
     *
     *****************************************/
    PFO_STCK_MA_DS200In  temporaryInput;
    PFO_STCK_MA_DS200Out temporaryOutput;
    bzero(&temporaryInput,  sizeof(PFO_STCK_MA_DS200In));
    bzero(&temporaryOutput, sizeof(PFO_STCK_MA_DS200Out));

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID20------------------
    /* 입력값 셋팅 */
    STRCPY(temporaryInput.mncm_code, context->btch_mncm_code);   // 운용사코드
    STRCPY(temporaryInput.fund_code, context->btch_fund_code);   // 펀드코드
    STRCPY(temporaryInput.proc_date, context->btch_proc_date);   // 처리일자
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID20--------------------

    /*****************************************
     * KIND    : DBIO Callee Info
     * NAME    : 주식 보유종목 상위조회
     * EXEC    : SELECT
     * INPUT   : PFO_STCK_MA_DS200In
     * OUTPUT  : PFO_STCK_MA_DS200Out
     *****************************************/
    PFM_TRYNJ(pfmDbioSelect("PFO_STCK_MA_DS200", &temporaryInput, &temporaryOutput, NULL, PFMDBIO_NOLOCK));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_EXCEPTION NODEID20------------------
    if( rc != RC_NRM && rc != RC_NFD)
    {
        PFM_SET_ERR("ZCOM00003", "PFO_STCK_MA_DS200");
        return RC_ERR;
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_EXCEPTION NODEID20--------------------

    }
    {
    /*****************************************
     * KIND    : DBIO Module Function Call
     * NODE ID : 30
     * NAME    : BM 산식템플릿 참조회
     * DESCRIPTION :
     *
     *****************************************/
    PFO_BM_STUP_TEMPLT_BS_DS011In  temporaryInput;
    PFO_BM_STUP_TEMPLT_BS_DS011Out temporaryOutput;
    bzero(&temporaryInput,  sizeof(PFO_BM_STUP_TEMPLT_BS_DS011In));
    bzero(&temporaryOutput, sizeof(PFO_BM_STUP_TEMPLT_BS_DS011Out));

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID30------------------
    /* 입력값 셋팅 */
    STRCPY(temporaryInput.mncm_code, context->btch_mncm_code);   // 운용사코드
    STRCPY(temporaryInput.fund_code, context->btch_fund_code);   // 펀드코드
    STRCPY(temporaryInput.end_date,  context->btch_end_date);    // 종료일자
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID30--------------------

    /*****************************************
     * KIND    : DBIO Callee Info
     * NAME    : BM 산식템플릿 참조회
     * EXEC    : SELECT
     * INPUT   : PFO_BM_STUP_TEMPLT_BS_DS011In
     * OUTPUT  : PFO_BM_STUP_TEMPLT_BS_DS011Out
     *****************************************/
    PFM_TRYNJ(pfmDbioSelect("PFO_BM_STUP_TEMPLT_BS_DS011", &temporaryInput, &temporaryOutput, NULL, PFMDBIO_NOLOCK));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_EXCEPTION NODEID30------------------
    if( rc != RC_NRM && rc != RC_NFD)
    {
        PFM_SET_ERR("ZCOM00003", "PFO_BM_STUP_TEMPLT_BS_DS011");
        return RC_ERR;
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_EXCEPTION NODEID30--------------------

    }
    {
    /*****************************************
     * KIND    : DBIO Module Function Call
     * NODE ID : 40
     * NAME    : 운용사 코드 이력 조회
     * DESCRIPTION :
     *
     *****************************************/
    PFO_MNCM_CLCD_HT_EI901In  temporaryInput;
    PFO_MNCM_CLCD_HT_EI901Out temporaryOutput;
    bzero(&temporaryInput,  sizeof(PFO_MNCM_CLCD_HT_EI901In));
    bzero(&temporaryOutput, sizeof(PFO_MNCM_CLCD_HT_EI901Out));

    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:BEFORE_CODE NODEID40------------------
    /* 입력값 셋팅 */
    STRCPY(temporaryInput.mncm_code, context->btch_mncm_code);   // 운용사코드
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:BEFORE_CODE NODEID40--------------------

    /*****************************************
     * KIND    : DBIO Callee Info
     * NAME    : 운용사 코드 이력 조회
     * EXEC    : SELECT
     * INPUT   : PFO_MNCM_CLCD_HT_EI901In
     * OUTPUT  : PFO_MNCM_CLCD_HT_EI901Out
     *****************************************/
    PFM_TRYNJ(pfmDbioSelect("PFO_MNCM_CLCD_HT_EI901", &temporaryInput, &temporaryOutput, NULL, PFMDBIO_NOLOCK));
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:DBIO_EXCEPTION NODEID40------------------
    if( rc != RC_NRM && rc != RC_NFD)
    {
        PFM_SET_ERR("ZCOM00003", "PFO_MNCM_CLCD_HT_EI901");
        return RC_ERR;
    }
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:DBIO_EXCEPTION NODEID40--------------------

    }
    {
    /*****************************************
     * KIND    : Virtual Module
     * NODE ID : 90
     * NAME    : 정상종료
     * DESCRIPTION :
     *
     *****************************************/
    //DO_NOT_MODIFY_THIS_LINE-----------START_OF_CODE:VIRTUAL_MODULE NODEID90-----------------
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE-----------END_OF_CODE:VIRTUAL_MODULE NODEID90-------------------

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}
