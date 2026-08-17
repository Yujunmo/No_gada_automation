"""
app/tools/table_extractor/refs.py 단위 테스트 (순수 함수, IO 무관).

콜 매크로별 캡처(dbio/biz/service/batch) + 등장순 정렬 + 중복 제거 + 주석 속
죽은 코드 오탐 방지를 고정한다. dbio/biz/batch 케이스는 실물 픽스처(remote_ap_server/files/)로,
service 케이스(pfmServiceModuleCall)는 현재 보유 픽스처에 실례가 없어 합성 텍스트로 고정한다.
"""
from __future__ import annotations

from pathlib import Path

from app.tools.table_extractor.refs import scan_module_refs

COMPILE_ROOT = (
    Path(__file__).resolve().parents[2]
    / "remote_ap_server" / "files" / "truap01dap1" / "proframe" / "proframe5.0" / "compile"
)


def test_dbio_calls_captured_in_order_no_dup():
    src = (COMPILE_ROOT / "PCOM/src/module/MPCOM_GetBzopDate.c").read_text("utf-8")
    refs = scan_module_refs(src)
    dbio_refs = [r for r in refs if r[0] == "dbio"]
    assert dbio_refs == [
        ("dbio", "PFO_DATE_MNGM_BS_VS004"),
        ("dbio", "PFO_DATE_MNGM_BS_VS005"),
        ("dbio", "PFO_DATE_MNGM_BS_VS006"),
        ("dbio", "PFO_DATE_MNGM_BS_VS007"),
        ("dbio", "PFO_DATE_MNGM_BS_VS008"),
        ("dbio", "PFO_DATE_MNGM_BS_VS009"),
        ("dbio", "PFO_DATE_MNGM_BS_VS010"),
        ("dbio", "PFO_DATE_MNGM_BS_VS011"),
    ]


def test_dbio_variants_opencursorarray_and_closecursorarray():
    src = (COMPILE_ROOT / "RLGR/src/serviceModule/SRLGR96602A/SRLGR96602A.c").read_text("utf-8")
    refs = {r for r in scan_module_refs(src) if r[0] == "dbio"}
    assert ("dbio", "RPT_RLGR_TM_VF701") in refs
    assert ("dbio", "PFO_FUND_INFR_HT_VF721") in refs
    assert ("dbio", "TRU_CMN_SRCH_SLCT_TM_EI001") in refs


def test_biz_call_captured():
    src = (COMPILE_ROOT / "PCSP/src/serviceModule/SPCSP53619C/SPCSP53619C.c").read_text("utf-8")
    refs = {r for r in scan_module_refs(src) if r[0] == "biz"}
    assert refs == {
        ("biz", "MPCOM_GetBzopDate"),
        ("biz", "MPCOM_CalcFndRntn"),
        ("biz", "MPCOM_CalcBmRnrt"),
    }


def test_batch_literal_and_biz_batchlinkcall_both_captured():
    # 실물 케이스: bat_code 대입문 리터럴("BRLGRPRP0001")이 batch로 잡히고,
    # 그걸 감싸는 pfmDlCall("MZPFM_BatchLinkCall", ...) 자체는 biz로도 같이 잡힌다
    # (그 이름의 소스 파일은 없어 재귀 중 skip되는 게 의도된 부분성공).
    src = (COMPILE_ROOT / "RLGR/src/serviceModule/SRLGR96602A/SRLGR96602A.c").read_text("utf-8")
    refs = scan_module_refs(src)
    assert ("batch", "BRLGRPRP0001") in refs
    assert ("biz", "MZPFM_BatchLinkCall") in refs


def test_dead_code_in_comment_not_captured():
    # SPCSP53619C.c 450번 줄: //pfmDbioCloseCursorArray("OK_IMSI_META_VF001"); /* Cursor close */
    src = (COMPILE_ROOT / "PCSP/src/serviceModule/SPCSP53619C/SPCSP53619C.c").read_text("utf-8")
    refs = scan_module_refs(src)
    assert ("dbio", "OK_IMSI_META_VF001") not in refs
    # 같은 파일의 살아있는 호출은 여전히 잡혀야 한다.
    assert ("dbio", "PFO_FUND_BS_DF036") in refs


def test_service_call_sizeof_in_struct_name():
    src = (
        'PFM_TRYNJ(pfmServiceModuleCall(&in, &out, &linkHeader, '
        'sizeof(SPCOM48990B_IN), &out, sizeof(SPCOM48990B_OUT)));'
    )
    assert scan_module_refs(src) == [("service", "SPCOM48990B")]


def test_bzero_sizeof_in_without_service_call_not_captured():
    # SPCSP53619C.c 실물 패턴: bzero(&temporaryInput, sizeof(MPCOM_GetBzopDate_IN))은
    # pfmServiceModuleCall이 아니라 pfmDlCall 앞의 입력구조체 초기화라 service로 오탐되면 안 됨.
    src = (
        'MPCOM_GetBzopDate_IN temporaryInput;\n'
        'bzero(&temporaryInput, sizeof(MPCOM_GetBzopDate_IN));\n'
        'PFM_TRYNJ(pfmDlCall("MPCOM_GetBzopDate", "MPCOM_GetBzopDate", &temporaryInput, &temporaryOutput));'
    )
    refs = scan_module_refs(src)
    assert ("service", "MPCOM_GetBzopDate") not in refs
    assert ("biz", "MPCOM_GetBzopDate") in refs


def test_duplicate_refs_deduped_keep_first_order():
    src = 'pfmDlCall("A"); pfmDlCall("B"); pfmDlCall("A");'
    assert scan_module_refs(src) == [("biz", "A"), ("biz", "B")]


def test_mixed_types_sorted_by_appearance_order():
    src = 'pfmDlCall("BIZ1"); pfmDbioSelect("DBIO1"); pfmDlCall("BIZ2");'
    assert scan_module_refs(src) == [
        ("biz", "BIZ1"),
        ("dbio", "DBIO1"),
        ("biz", "BIZ2"),
    ]


def test_no_refs_returns_empty():
    assert scan_module_refs("int main() { return 0; }") == []
