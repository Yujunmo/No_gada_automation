/*
 * @file        MPCOM_GetBzopDate.c
 * @filetype    c source file
 * @brief       영업일조회
 * @author      151397
 * @version
 * @dep-header
 * @history
 *      Version:    Name :  Date :      Reference :        Desciption :
 *      ------      ----    ----        ---------          ----------
 *      VER1.00 : 151397 : 20230706 : proframe 구축     : 신규 개발
 *
 */
/*******************************************************
 * KIND    : BIZ_MODULEModule Interface
 * NODE ID : 0
 * NAME    : 영업일조회
 * DESCRIPTION :
 *
 *******************************************************/

#include "MPCOM_GetBzopDate.h"

static MapperMapInfo mappingInfo = {PMAP_FLAG_TRACE_ON, 0, "", "", "", "", ""};

#if defined (__cplusplus)
extern "C"
#endif

/*******************************************************
 * COMMENTS :
 *   영업일조회
 *******************************************************/

long MPCOM_GetBzopDate(MPCOM_GetBzopDate_IN *input, MPCOM_GetBzopDate_OUT *output)
{
    MPCOM_GetBzopDateContext  __context;
    MPCOM_GetBzopDateContext *context = &__context;

    long rc = RC_NRM;

    bzero(context, sizeof(MPCOM_GetBzopDateContext));
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
static long init_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    {
    /*******************************************************
     * KIND    : Virtual Module
     * NODE ID : 6
     * NAME    : 초기화
     * DESCRIPTION :
     *
     *******************************************************/
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:VIRTUAL_MODULE
    //NODEID6------------//
    // TODO Auto-generated method stub
    /* 입력구조체 debug 로그출력 ( PRINT_구조체명(&변수명) ) */
    PRINT_MPCOM_GetBzopDate_IN(INPUT);
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:VIRTUAL_MODULE NODEID6------------//

    }

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
static long input_valid_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    {
    /*******************************************************
     * KIND    : Virtual Module
     * NODE ID : 7
     * NAME    : 입력값 검증
     * DESCRIPTION :
     *
     *******************************************************/
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:VIRTUAL_MODULE
    //NODEID7------------//
    // TODO Auto-generated method stub

    /* 필수 입력값 체크 */
    /* PFM_CHECK_ISSPNULL(문자열 필드, 메시지코드, 메시지코드 format string ); */
    //PFM_CHECK_ISSPNULL( INPUT->prsn_date, "ZCOM00001", "현재일자");

    /* PFM_CHECK_ISZERO(long형 필드, 메시지코드, 메시지코드 format string ); */
    //PFM_CHECK_ISZERO( INPUT->calc_dycn, "ZCOM00001", "계산일수");

    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:VIRTUAL_MODULE NODEID7------------//

    }

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
static long main_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    if(
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_CONDITION
    //NODEID11------------//
    // TODO Auto-generated method stub
    INPUT->calc_dycn > 0
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_CONDITION
    //NODEID11------------//
    )
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 11
     * NAME    : 이후
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(aft_select_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID11------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID11------------//

    }
    else if(
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:VIRTUAL_MODULE_CONDITION
    //NODEID39------------//
    // TODO Auto-generated method stub
    INPUT->calc_dycn == 0
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:VIRTUAL_MODULE_CONDITION
    //NODEID39------------//
    )
    {
    /*******************************************************
     * KIND    : Virtual Module
     * NODE ID : 39
     * NAME    : 0이면 현재일자
     * DESCRIPTION :
     *
     *******************************************************/
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:VIRTUAL_MODULE
    //NODEID39------------//
    // TODO Auto-generated method stub
    /* 출력값 셋팅 */
    STRCPY(OUTPUT->bzop_date, INPUT->prsn_date); // 영업일자 <- 현재일자
    PFM_DBG("[영업일자[%s]", OUTPUT->bzop_date);
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:VIRTUAL_MODULE NODEID39------------//

    }
    else if(
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_CONDITION
    //NODEID12------------//
    // TODO Auto-generated method stub
    INPUT->calc_dycn < 0
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_CONDITION
    //NODEID12------------//
    )
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 12
     * NAME    : 이전
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(bfr_select_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID12------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID12------------//

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 11
 * NAME    : 이후
 * DESCRIPTION :
 *
 *******************************************************/
static long aft_select_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    if(
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_CONDITION
    //NODEID22------------//
    // TODO Auto-generated method stub
    STRCMP(INPUT->ntrd_incs_yn, "Y") == 0
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_CONDITION
    //NODEID22------------//
    )
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 22
     * NAME    : 휴장 포함
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(aft_ntrd_y_select_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID22------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID22------------//

    }
    else
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 21
     * NAME    : 휴장 미포함
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(aft_ntrd_n_select_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID21------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID21------------//

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 22
 * NAME    : 휴장 포함
 * DESCRIPTION :
 *
 *******************************************************/
static long aft_ntrd_y_select_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    if(
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_CONDITION
    //NODEID9------------//
    // TODO Auto-generated method stub
    STRCMP(INPUT->thdy_incs_yn, "Y") == 0
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_CONDITION
    //NODEID9------------//
    )
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 9
     * NAME    : 당일 포함
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(aft_ntrd_y_thdy_y_select_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID9------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID9------------//

    }
    else
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 10
     * NAME    : 당일 미포함
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(aft_ntrd_y_thdy_n_select_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID10------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID10------------//

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 9
 * NAME    : 당일 포함
 * DESCRIPTION :
 *
 *******************************************************/
static long aft_ntrd_y_thdy_y_select_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    {
    /*******************************************************
     * KIND    : DBIO Call
     * NODE ID : 14
     * NAME    : PCOM_일자_관리_기본 단건조회 이후 휴장포함 당일포함 영업일조회
     * DESCRIPTION :
     *
     *******************************************************/
    PFO_DATE_MNGM_BS_VS004In  temporaryInput;
    PFO_DATE_MNGM_BS_VS004Out temporaryOutput;

    bzero(&temporaryInput,  sizeof(PFO_DATE_MNGM_BS_VS004In));
    bzero(&temporaryOutput, sizeof(PFO_DATE_MNGM_BS_VS004Out));

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER
    //NODEID14------------//
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER
    //NODEID14------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:BEFORE_CODE NODEID14------------//
    // TODO Auto-generated method stub

    /* 입력값 셋팅 */
    STRCPY(temporaryInput.prsn_date , INPUT->prsn_date);    // 현재일자
    temporaryInput.calc_dycn        = INPUT->calc_dycn;     // 계산일수

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_DATE_MNGM_BS_VS004_INPUT(&temporaryInput);
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:BEFORE_CODE NODEID14------------//

    /*******************************************************
     * KIND              : DBIO Callee Info
     * NAME              : PCOM_일자_관리_기본 단건조회 이후 휴장포함 당일포함 영업일조회
     * EXEC              : SELECT
     * INPUT             : PFO_DATE_MNGM_BS_VS004In
     * OUTPUT            : PFO_DATE_MNGM_BS_VS004Out
     * ARRAY INPUT       : NONE
     * ARRAY OUTPUT      : NONE
     * DYNAMIC STRUCTURE : NONE
     *******************************************************/
    PFM_TRYNJ(pfmDbioSelect("PFO_DATE_MNGM_BS_VS004", &temporaryInput, &temporaryOutput, NULL, PFMDBIO_NOLOCK));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_EXCEPTION NODEID14------------//

    if( rc != RC_NRM) /* DBIO 예외처리 */
    {
        if( rc == RC_NFD)
        {
            PFM_DBG("[FAIL] DBIO : select data not found!!! "); /* 조회조건에 맞는 값이 없음 */
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
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_EXCEPTION NODEID14------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:AFTER_CODE NODEID14------------//
    // TODO Auto-generated method stub

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_DATE_MNGM_BS_VS004_OUTPUT(&temporaryOutput);

    /* 출력값 셋팅 */
    STRCPY(OUTPUT->bzop_date, temporaryOutput.bzop_date); // 영업일자
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:AFTER_CODE NODEID14------------//

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 10
 * NAME    : 당일 미포함
 * DESCRIPTION :
 *
 *******************************************************/
static long aft_ntrd_y_thdy_n_select_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    {
    /*******************************************************
     * KIND    : DBIO Call
     * NODE ID : 18
     * NAME    : PCOM_일자_관리_기본 단건조회 이후 휴장포함 당일미포함 영업일조회
     * DESCRIPTION :
     *
     *******************************************************/
    PFO_DATE_MNGM_BS_VS005In  temporaryInput;
    PFO_DATE_MNGM_BS_VS005Out temporaryOutput;

    bzero(&temporaryInput,  sizeof(PFO_DATE_MNGM_BS_VS005In));
    bzero(&temporaryOutput, sizeof(PFO_DATE_MNGM_BS_VS005Out));

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER
    //NODEID18------------//
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER
    //NODEID18------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:BEFORE_CODE NODEID18------------//
    // TODO Auto-generated method stub

    /* 입력값 셋팅 */
    STRCPY(temporaryInput.prsn_date , INPUT->prsn_date);    // 현재일자
    temporaryInput.calc_dycn        = INPUT->calc_dycn;     // 계산일수

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_DATE_MNGM_BS_VS005_INPUT(&temporaryInput);
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:BEFORE_CODE NODEID18------------//

    /*******************************************************
     * KIND              : DBIO Callee Info
     * NAME              : PCOM_일자_관리_기본 단건조회 이후 휴장포함 당일미포함 영업일조회
     * EXEC              : SELECT
     * INPUT             : PFO_DATE_MNGM_BS_VS005In
     * OUTPUT            : PFO_DATE_MNGM_BS_VS005Out
     * ARRAY INPUT       : NONE
     * ARRAY OUTPUT      : NONE
     * DYNAMIC STRUCTURE : NONE
     *******************************************************/
    PFM_TRYNJ(pfmDbioSelect("PFO_DATE_MNGM_BS_VS005", &temporaryInput, &temporaryOutput, NULL, PFMDBIO_NOLOCK));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_EXCEPTION NODEID18------------//

    if( rc != RC_NRM) /* DBIO 예외처리 */
    {
        if( rc == RC_NFD)
        {
            PFM_DBG("[FAIL] DBIO : select data not found!!! "); /* 조회조건에 맞는 값이 없음 */
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
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_EXCEPTION NODEID18------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:AFTER_CODE NODEID18------------//
    // TODO Auto-generated method stub

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_DATE_MNGM_BS_VS005_OUTPUT(&temporaryOutput);

    /* 출력값 셋팅 */
    STRCPY(OUTPUT->bzop_date, temporaryOutput.bzop_date); // 영업일자
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:AFTER_CODE NODEID18------------//

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 21
 * NAME    : 휴장 미포함
 * DESCRIPTION :
 *
 *******************************************************/
static long aft_ntrd_n_select_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    if(
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_CONDITION
    //NODEID24------------//
    // TODO Auto-generated method stub
    STRCMP(INPUT->thdy_incs_yn, "Y") == 0
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_CONDITION
    //NODEID24------------//
    )
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 24
     * NAME    : 당일 포함
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(aft_ntrd_n_thdy_y_select_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID24------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID24------------//

    }
    else
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 25
     * NAME    : 당일 미포함
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(aft_ntrd_n_thdy_n_select_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID25------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID25------------//

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 24
 * NAME    : 당일 포함
 * DESCRIPTION :
 *
 *******************************************************/
static long aft_ntrd_n_thdy_y_select_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    {
    /*******************************************************
     * KIND    : DBIO Call
     * NODE ID : 17
     * NAME    : PCOM_일자_관리_기본 단건조회 이후 휴장미포함 당일포함 영업일조회
     * DESCRIPTION :
     *
     *******************************************************/
    PFO_DATE_MNGM_BS_VS006In  temporaryInput;
    PFO_DATE_MNGM_BS_VS006Out temporaryOutput;

    bzero(&temporaryInput,  sizeof(PFO_DATE_MNGM_BS_VS006In));
    bzero(&temporaryOutput, sizeof(PFO_DATE_MNGM_BS_VS006Out));

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER
    //NODEID17------------//
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER
    //NODEID17------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:BEFORE_CODE NODEID17------------//
    // TODO Auto-generated method stub

    /* 입력값 셋팅 */
    STRCPY(temporaryInput.prsn_date , INPUT->prsn_date);    // 현재일자
    temporaryInput.calc_dycn        = INPUT->calc_dycn;     // 계산일수

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_DATE_MNGM_BS_VS006_INPUT(&temporaryInput);
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:BEFORE_CODE NODEID17------------//

    /*******************************************************
     * KIND              : DBIO Callee Info
     * NAME              : PCOM_일자_관리_기본 단건조회 이후 휴장미포함 당일포함 영업일조회
     * EXEC              : SELECT
     * INPUT             : PFO_DATE_MNGM_BS_VS006In
     * OUTPUT            : PFO_DATE_MNGM_BS_VS006Out
     * ARRAY INPUT       : NONE
     * ARRAY OUTPUT      : NONE
     * DYNAMIC STRUCTURE : NONE
     *******************************************************/
    PFM_TRYNJ(pfmDbioSelect("PFO_DATE_MNGM_BS_VS006", &temporaryInput, &temporaryOutput, NULL, PFMDBIO_NOLOCK));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_EXCEPTION NODEID17------------//

    if( rc != RC_NRM) /* DBIO 예외처리 */
    {
        if( rc == RC_NFD)
        {
            PFM_DBG("[FAIL] DBIO : select data not found!!! "); /* 조회조건에 맞는 값이 없음 */
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
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_EXCEPTION NODEID17------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:AFTER_CODE NODEID17------------//
    // TODO Auto-generated method stub

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_DATE_MNGM_BS_VS006_OUTPUT(&temporaryOutput);

    /* 출력값 셋팅 */
    STRCPY(OUTPUT->bzop_date, temporaryOutput.bzop_date); // 영업일자
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:AFTER_CODE NODEID17------------//

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 25
 * NAME    : 당일 미포함
 * DESCRIPTION :
 *
 *******************************************************/
static long aft_ntrd_n_thdy_n_select_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    {
    /*******************************************************
     * KIND    : DBIO Call
     * NODE ID : 19
     * NAME    : PCOM_일자_관리_기본 단건조회 이후 휴장미포함 당일미포함 영업일조회
     * DESCRIPTION :
     *
     *******************************************************/
    PFO_DATE_MNGM_BS_VS007In  temporaryInput;
    PFO_DATE_MNGM_BS_VS007Out temporaryOutput;

    bzero(&temporaryInput,  sizeof(PFO_DATE_MNGM_BS_VS007In));
    bzero(&temporaryOutput, sizeof(PFO_DATE_MNGM_BS_VS007Out));

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER
    //NODEID19------------//
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER
    //NODEID19------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:BEFORE_CODE NODEID19------------//
    // TODO Auto-generated method stub

    /* 입력값 셋팅 */
    STRCPY(temporaryInput.prsn_date , INPUT->prsn_date);    // 현재일자
    temporaryInput.calc_dycn        = INPUT->calc_dycn;     // 계산일수

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_DATE_MNGM_BS_VS007_INPUT(&temporaryInput);
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:BEFORE_CODE NODEID19------------//

    /*******************************************************
     * KIND              : DBIO Callee Info
     * NAME              : PCOM_일자_관리_기본 단건조회 이후 휴장미포함 당일미포함 영업일조회
     * EXEC              : SELECT
     * INPUT             : PFO_DATE_MNGM_BS_VS007In
     * OUTPUT            : PFO_DATE_MNGM_BS_VS007Out
     * ARRAY INPUT       : NONE
     * ARRAY OUTPUT      : NONE
     * DYNAMIC STRUCTURE : NONE
     *******************************************************/
    PFM_TRYNJ(pfmDbioSelect("PFO_DATE_MNGM_BS_VS007", &temporaryInput, &temporaryOutput, NULL, PFMDBIO_NOLOCK));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_EXCEPTION NODEID19------------//

    if( rc != RC_NRM) /* DBIO 예외처리 */
    {
        if( rc == RC_NFD)
        {
            PFM_DBG("[FAIL] DBIO : select data not found!!! "); /* 조회조건에 맞는 값이 없음 */
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
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_EXCEPTION NODEID19------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:AFTER_CODE NODEID19------------//
    // TODO Auto-generated method stub

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_DATE_MNGM_BS_VS007_OUTPUT(&temporaryOutput);

    /* 출력값 셋팅 */
    STRCPY(OUTPUT->bzop_date, temporaryOutput.bzop_date); // 영업일자
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:AFTER_CODE NODEID19------------//

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 12
 * NAME    : 이전
 * DESCRIPTION :
 *
 *******************************************************/
static long bfr_select_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    if(
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_CONDITION
    //NODEID20------------//
    // TODO Auto-generated method stub
    STRCMP(INPUT->ntrd_incs_yn, "Y") == 0
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_CONDITION
    //NODEID20------------//
    )
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 20
     * NAME    : 휴장 포함
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(bfr_ntrd_y_select_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID20------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID20------------//

    }
    else
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 23
     * NAME    : 휴장 미포함
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(bfr_ntrd_n_select_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID23------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID23------------//

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 20
 * NAME    : 휴장 포함
 * DESCRIPTION :
 *
 *******************************************************/
static long bfr_ntrd_y_select_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    if(
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_CONDITION
    //NODEID15------------//
    // TODO Auto-generated method stub
    STRCMP(INPUT->thdy_incs_yn, "Y") == 0
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_CONDITION
    //NODEID15------------//
    )
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 15
     * NAME    : 당일 포함
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(bfr_ntrd_y_thdy_y_select_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID15------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID15------------//

    }
    else
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 16
     * NAME    : 당일 미포함
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(bfr_ntrd_y_thdy_n_select_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID16------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID16------------//

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 15
 * NAME    : 당일 포함
 * DESCRIPTION :
 *
 *******************************************************/
static long bfr_ntrd_y_thdy_y_select_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    {
    /*******************************************************
     * KIND    : DBIO Call
     * NODE ID : 26
     * NAME    : PCOM_일자_관리_기본 단건조회 이전 휴장포함 당일포함 영업일조회
     * DESCRIPTION :
     *
     *******************************************************/
    PFO_DATE_MNGM_BS_VS008In  temporaryInput;
    PFO_DATE_MNGM_BS_VS008Out temporaryOutput;

    bzero(&temporaryInput,  sizeof(PFO_DATE_MNGM_BS_VS008In));
    bzero(&temporaryOutput, sizeof(PFO_DATE_MNGM_BS_VS008Out));

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER
    //NODEID26------------//
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER
    //NODEID26------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:BEFORE_CODE NODEID26------------//
    // TODO Auto-generated method stub

    /* 입력값 셋팅 */
    STRCPY(temporaryInput.prsn_date , INPUT->prsn_date);    // 현재일자
    temporaryInput.calc_dycn        = INPUT->calc_dycn;     // 계산일수

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_DATE_MNGM_BS_VS008_INPUT(&temporaryInput);
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:BEFORE_CODE NODEID26------------//

    /*******************************************************
     * KIND              : DBIO Callee Info
     * NAME              : PCOM_일자_관리_기본 단건조회 이전 휴장포함 당일포함 영업일조회
     * EXEC              : SELECT
     * INPUT             : PFO_DATE_MNGM_BS_VS008In
     * OUTPUT            : PFO_DATE_MNGM_BS_VS008Out
     * ARRAY INPUT       : NONE
     * ARRAY OUTPUT      : NONE
     * DYNAMIC STRUCTURE : NONE
     *******************************************************/
    PFM_TRYNJ(pfmDbioSelect("PFO_DATE_MNGM_BS_VS008", &temporaryInput, &temporaryOutput, NULL, PFMDBIO_NOLOCK));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_EXCEPTION NODEID26------------//

    if( rc != RC_NRM) /* DBIO 예외처리 */
    {
        if( rc == RC_NFD)
        {
            PFM_DBG("[FAIL] DBIO : select data not found!!! "); /* 조회조건에 맞는 값이 없음 */
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
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_EXCEPTION NODEID26------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:AFTER_CODE NODEID26------------//
    // TODO Auto-generated method stub

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_DATE_MNGM_BS_VS008_OUTPUT(&temporaryOutput);

    /* 출력값 셋팅 */
    STRCPY(OUTPUT->bzop_date, temporaryOutput.bzop_date); // 영업일자
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:AFTER_CODE NODEID26------------//

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 16
 * NAME    : 당일 미포함
 * DESCRIPTION :
 *
 *******************************************************/
static long bfr_ntrd_y_thdy_n_select_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    {
    /*******************************************************
     * KIND    : DBIO Call
     * NODE ID : 27
     * NAME    : PCOM_일자_관리_기본 단건조회 이전 휴장포함 당일미포함 영업일조회
     * DESCRIPTION :
     *
     *******************************************************/
    PFO_DATE_MNGM_BS_VS009In  temporaryInput;
    PFO_DATE_MNGM_BS_VS009Out temporaryOutput;

    bzero(&temporaryInput,  sizeof(PFO_DATE_MNGM_BS_VS009In));
    bzero(&temporaryOutput, sizeof(PFO_DATE_MNGM_BS_VS009Out));

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER
    //NODEID27------------//
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER
    //NODEID27------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:BEFORE_CODE NODEID27------------//
    // TODO Auto-generated method stub

    /* 입력값 셋팅 */
    STRCPY(temporaryInput.prsn_date , INPUT->prsn_date);    // 현재일자
    temporaryInput.calc_dycn        = INPUT->calc_dycn;     // 계산일수

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_DATE_MNGM_BS_VS009_INPUT(&temporaryInput);
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:BEFORE_CODE NODEID27------------//

    /*******************************************************
     * KIND              : DBIO Callee Info
     * NAME              : PCOM_일자_관리_기본 단건조회 이전 휴장포함 당일미포함 영업일조회
     * EXEC              : SELECT
     * INPUT             : PFO_DATE_MNGM_BS_VS009In
     * OUTPUT            : PFO_DATE_MNGM_BS_VS009Out
     * ARRAY INPUT       : NONE
     * ARRAY OUTPUT      : NONE
     * DYNAMIC STRUCTURE : NONE
     *******************************************************/
    PFM_TRYNJ(pfmDbioSelect("PFO_DATE_MNGM_BS_VS009", &temporaryInput, &temporaryOutput, NULL, PFMDBIO_NOLOCK));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_EXCEPTION NODEID27------------//

    if( rc != RC_NRM) /* DBIO 예외처리 */
    {
        if( rc == RC_NFD)
        {
            PFM_DBG("[FAIL] DBIO : select data not found!!! "); /* 조회조건에 맞는 값이 없음 */
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
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_EXCEPTION NODEID27------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:AFTER_CODE NODEID27------------//
    // TODO Auto-generated method stub

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_DATE_MNGM_BS_VS009_OUTPUT(&temporaryOutput);

    /* 출력값 셋팅 */
    STRCPY(OUTPUT->bzop_date, temporaryOutput.bzop_date); // 영업일자
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:AFTER_CODE NODEID27------------//

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 23
 * NAME    : 휴장 미포함
 * DESCRIPTION :
 *
 *******************************************************/
static long bfr_ntrd_n_select_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    if(
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_CONDITION
    //NODEID28------------//
    // TODO Auto-generated method stub
    STRCMP(INPUT->thdy_incs_yn, "Y") == 0
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_CONDITION
    //NODEID28------------//
    )
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 28
     * NAME    : 당일 포함
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(bfr_ntrd_n_thdy_y_select_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID28------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID28------------//

    }
    else
    {
    /*******************************************************
     * KIND    : Intermediary Module Function Call
     * NODE ID : 29
     * NAME    : 당일 미포함
     * DESCRIPTION :
     *
     *******************************************************/
    PFM_TRY(bfr_ntrd_n_thdy_n_select_proc(context));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID29------------//
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:INNER_MODULE_EXCEPTION
    //NODEID29------------//

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 28
 * NAME    : 당일 포함
 * DESCRIPTION :
 *
 *******************************************************/
static long bfr_ntrd_n_thdy_y_select_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    {
    /*******************************************************
     * KIND    : DBIO Call
     * NODE ID : 30
     * NAME    : PCOM_일자_관리_기본 단건조회 이전 휴장미포함 당일포함 영업일조회
     * DESCRIPTION :
     *
     *******************************************************/
    PFO_DATE_MNGM_BS_VS010In  temporaryInput;
    PFO_DATE_MNGM_BS_VS010Out temporaryOutput;

    bzero(&temporaryInput,  sizeof(PFO_DATE_MNGM_BS_VS010In));
    bzero(&temporaryOutput, sizeof(PFO_DATE_MNGM_BS_VS010Out));

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER
    //NODEID30------------//
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER
    //NODEID30------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:BEFORE_CODE NODEID30------------//
    // TODO Auto-generated method stub

    /* 입력값 셋팅 */
    STRCPY(temporaryInput.prsn_date , INPUT->prsn_date);    // 현재일자
    temporaryInput.calc_dycn        = INPUT->calc_dycn;     // 계산일수

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_DATE_MNGM_BS_VS010_INPUT(&temporaryInput);
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:BEFORE_CODE NODEID30------------//

    /*******************************************************
     * KIND              : DBIO Callee Info
     * NAME              : PCOM_일자_관리_기본 단건조회 이전 휴장미포함 당일포함 영업일조회
     * EXEC              : SELECT
     * INPUT             : PFO_DATE_MNGM_BS_VS010In
     * OUTPUT            : PFO_DATE_MNGM_BS_VS010Out
     * ARRAY INPUT       : NONE
     * ARRAY OUTPUT      : NONE
     * DYNAMIC STRUCTURE : NONE
     *******************************************************/
    PFM_TRYNJ(pfmDbioSelect("PFO_DATE_MNGM_BS_VS010", &temporaryInput, &temporaryOutput, NULL, PFMDBIO_NOLOCK));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_EXCEPTION NODEID30------------//

    if( rc != RC_NRM) /* DBIO 예외처리 */
    {
        if( rc == RC_NFD)
        {
            PFM_DBG("[FAIL] DBIO : select data not found!!! "); /* 조회조건에 맞는 값이 없음 */
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
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_EXCEPTION NODEID30------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:AFTER_CODE NODEID30------------//
    // TODO Auto-generated method stub

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_DATE_MNGM_BS_VS010_OUTPUT(&temporaryOutput);

    /* 출력값 셋팅 */
    STRCPY(OUTPUT->bzop_date, temporaryOutput.bzop_date); // 영업일자
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:AFTER_CODE NODEID30------------//

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}

/*******************************************************
 * KIND    : Intermediary Module Function
 * NODE ID : 29
 * NAME    : 당일 미포함
 * DESCRIPTION :
 *
 *******************************************************/
static long bfr_ntrd_n_thdy_n_select_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    {
    /*******************************************************
     * KIND    : DBIO Call
     * NODE ID : 31
     * NAME    : PCOM_일자_관리_기본 단건조회 이전 휴장미포함 당일미포함 영업일조회
     * DESCRIPTION :
     *
     *******************************************************/
    PFO_DATE_MNGM_BS_VS011In  temporaryInput;
    PFO_DATE_MNGM_BS_VS011Out temporaryOutput;

    bzero(&temporaryInput,  sizeof(PFO_DATE_MNGM_BS_VS011In));
    bzero(&temporaryOutput, sizeof(PFO_DATE_MNGM_BS_VS011Out));

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_DYNAMIC_PARAMETER
    //NODEID31------------//
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_DYNAMIC_PARAMETER
    //NODEID31------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:BEFORE_CODE NODEID31------------//
    // TODO Auto-generated method stub

    /* 입력값 셋팅 */
    STRCPY(temporaryInput.prsn_date , INPUT->prsn_date);    // 현재일자
    temporaryInput.calc_dycn        = INPUT->calc_dycn;     // 계산일수

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_DATE_MNGM_BS_VS011_INPUT(&temporaryInput);
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:BEFORE_CODE NODEID31------------//

    /*******************************************************
     * KIND              : DBIO Callee Info
     * NAME              : PCOM_일자_관리_기본 단건조회 이전 휴장미포함 당일미포함 영업일조회
     * EXEC              : SELECT
     * INPUT             : PFO_DATE_MNGM_BS_VS011In
     * OUTPUT            : PFO_DATE_MNGM_BS_VS011Out
     * ARRAY INPUT       : NONE
     * ARRAY OUTPUT      : NONE
     * DYNAMIC STRUCTURE : NONE
     *******************************************************/
    PFM_TRYNJ(pfmDbioSelect("PFO_DATE_MNGM_BS_VS011", &temporaryInput, &temporaryOutput, NULL, PFMDBIO_NOLOCK));
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:DBIO_EXCEPTION NODEID31------------//

    if( rc != RC_NRM) /* DBIO 예외처리 */
    {
        if( rc == RC_NFD)
        {
            PFM_DBG("[FAIL] DBIO : select data not found!!! "); /* 조회조건에 맞는 값이 없음 */
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
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:DBIO_EXCEPTION NODEID31------------//

    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:AFTER_CODE NODEID31------------//
    // TODO Auto-generated method stub

    /* DBIO구조체 debug로그 print */
    PRINT_PFO_DATE_MNGM_BS_VS011_OUTPUT(&temporaryOutput);

    /* 출력값 셋팅 */
    STRCPY(OUTPUT->bzop_date, temporaryOutput.bzop_date); // 영업일자
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:AFTER_CODE NODEID31------------//

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
static long norm_exit_proc(MPCOM_GetBzopDateContext *context)
{
    long rc = RC_NRM;

    // User Variables Declaration

    {
    /*******************************************************
     * KIND    : Virtual Module
     * NODE ID : 8
     * NAME    : 정상처리
     * DESCRIPTION :
     *
     *******************************************************/
    //DO_NOT_MODIFY_THIS_LINE----------START_OF_CODE:VIRTUAL_MODULE
    //NODEID8------------//
    // TODO Auto-generated method stub
    //DO_NOT_MODIFY_THIS_LINE----------END_OF_CODE:VIRTUAL_MODULE NODEID8------------//

    }

    return RC_NRM;

PFM_CATCH:
    return rc;
}
