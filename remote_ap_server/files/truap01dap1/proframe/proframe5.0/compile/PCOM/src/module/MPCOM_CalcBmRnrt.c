/*
 * @file        MPCOM_CalcBmRnrt.c
 * @filetype    c source file
 * @brief       BM(벤치마크) 수익률 계산
 * @author      151397
 * @version
 * @dep-header
 * @history
 *      Version:    Name :  Date :      Reference :        Desciption :
 *      ------      ----    ----        ---------          ----------
 *      VER1.00 : 151397 : 20260618 : proframe 구축     : 신규 개발
 *
 */
/*******************************************************
 * KIND    : BIZ_MODULEModule Interface
 * NODE ID : 0
 * NAME    : BM(벤치마크) 수익률 계산
 * DESCRIPTION :
 *
 *******************************************************/

#include "MPCOM_CalcBmRnrt.h"

static MapperMapInfo mappingInfo = {PMAP_FLAG_TRACE_ON, 0, "", "", "", "", ""};

#if defined (__cplusplus)
extern "C"
#endif

/*******************************************************
 * COMMENTS :
 *   BM(벤치마크) 수익률 계산
 *******************************************************/

long MPCOM_CalcBmRnrt(MPCOM_CalcBmRnrt_IN *input, MPCOM_CalcBmRnrt_OUT *output)
{
    MPCOM_CalcBmRnrtContext  __context;
    MPCOM_CalcBmRnrtContext *context = &__context;

    long rc = RC_NRM;

    bzero(context, sizeof(MPCOM_CalcBmRnrtContext));
    context->input  = input;
    context->output = output;

    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 1
     * NAME    : 초기화
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(init_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID1------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID1------------//

    }
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 2
     * NAME    : 입력검증
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(input_valid_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID2------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID2------------//

    }
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 3
     * NAME    : 본처리
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(main_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID3------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID3------------//

    }
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 4
     * NAME    : 정상종료
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(norm_exit_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID4------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID4------------//

    }

    return RC_NRM;

PFM_CATCH:
    {
    /*******************************************************
     * KIND    : Virtual Module
     * NODE ID : 5
     * NAME    : 예외처리
     * DESCRIPTION :
     *
     *******************************************************/
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:VIRTUAL_MODULE
    //NODEID5------------//
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:VIRTUAL_MODULE NODEID5------------//

    }

    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 1
 * NAME    : 초기화
 * DESCRIPTION :
 *
 *******************************************************/
static long init_proc(MPCOM_CalcBmRnrtContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 2
 * NAME    : 입력검증
 * DESCRIPTION :
 *
 *******************************************************/
static long input_valid_proc(MPCOM_CalcBmRnrtContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 3
 * NAME    : 본처리
 * DESCRIPTION :
 *
 *******************************************************/
static long main_proc(MPCOM_CalcBmRnrtContext *context)
{
    long rc = RC_NRM;

    {
    /*******************************************************
     * KIND    : DBIO Module Function Call
     * NODE ID : 10
     * NAME    : BM 수익률 계산용 이력조회
     * DESCRIPTION :
     *
     *******************************************************/
    PFO_BM_RNRT_HT_DS103In  temporaryInput;
    PFO_BM_RNRT_HT_DS103Out temporaryOutput;
    bzero(&temporaryInput,  sizeof(PFO_BM_RNRT_HT_DS103In));
    bzero(&temporaryOutput, sizeof(PFO_BM_RNRT_HT_DS103Out));

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:BEFORE_CODE NODEID10------------//
    /* 입력값 셋팅 */
    STRCPY(temporaryInput.mncm_code,      INPUT->mncm_code);        // 운용사코드
    STRCPY(temporaryInput.bm_templt_code, INPUT->bm_templt_code);   // BM 템플릿코드
    STRCPY(temporaryInput.strn_date,      INPUT->strn_date);        // 시작일자
    STRCPY(temporaryInput.end_date,       INPUT->end_date);         // 종료일자

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_BM_RNRT_HT_DS103_INPUT(&temporaryInput);
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:BEFORE_CODE NODEID10------------//

    /*******************************************************
     * KIND              : DBIO Callee Info
     * NAME              : BM 수익률 계산용 이력조회
     * EXEC              : SELECT
     * INPUT             : PFO_BM_RNRT_HT_DS103In
     * OUTPUT            : PFO_BM_RNRT_HT_DS103Out
     * ARRAY INPUT       : NONE
     * ARRAY OUTPUT      : YES
     * DYNAMIC STRUCTURE : NONE
     *******************************************************/
    PFM_TRYNJ(pfmDbioOpenCursorArray("PFO_BM_RNRT_HT_DS103", &temporaryInput, &temporaryOutput, NULL, PFMDBIO_NOLOCK));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_EXCEPTION NODEID10------------//

    if( rc != RC_NRM) /* DBIO 예외처리 */
    {
        if( rc == RC_NFD)
        {
            PFM_DBG("[FAIL] DBIO : select data not found!!! "); /* 조회조건에 맞는 값이 없음 */
            /* ZCOM00003 : 해당 조건의 데이터가 없습니다. */
            PFM_SET_MSG("ZCOM00003");
            return RC_NRM;
        }
        PFM_ERR( "[FAIL] DBIO error [%ld][%s]", PDB_ERRORNUM, PDB_ERRORSTR);
        PFM_SET_ERR("ZCOM00014", PDB_ERRORSTR);
        return RC_ERR;
    }
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_EXCEPTION NODEID10--------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:AFTER_CODE NODEID10------------//
    // TODO Auto-generated method stub: 조회된 이력으로 BM 수익률 계산
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:AFTER_CODE NODEID10--------------//

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 4
 * NAME    : 정상종료
 * DESCRIPTION :
 *
 *******************************************************/
static long norm_exit_proc(MPCOM_CalcBmRnrtContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    return RC_NRM;

PFM_CATCH:
    return rc;
}
