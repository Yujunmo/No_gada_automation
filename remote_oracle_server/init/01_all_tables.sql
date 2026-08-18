-- all_tables: 테이블명 → PK 컬럼명 매핑 (복합키는 테이블당 여러 행 → PK 제약 없음)
-- remote_db_server/init/01_all_tables.sql과 동일한 시드 데이터를 Oracle DDL/DML로 포팅.
-- gvenzl 이미지의 init 스크립트는 SYS로 CDB 루트에 접속하므로 PDB 진입 + 스키마 전환이 필요하다.
ALTER SESSION SET CONTAINER = NOGADA;
ALTER SESSION SET CURRENT_SCHEMA = TESTUSER;

CREATE TABLE all_tables (
  table_id   VARCHAR2(30) NOT NULL,
  pk_column  VARCHAR2(30) NOT NULL
);

INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_STCK_MA', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_STCK_MA', 'fund_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_STCK_MA', 'proc_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_STCK_MA', 'itms_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_BRWN_STCK_MA', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_BRWN_STCK_MA', 'fund_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_BRWN_STCK_MA', 'proc_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_BRWN_STCK_MA', 'itms_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_SPA_MA', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_SPA_MA', 'fund_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_SPA_MA', 'proc_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_SPA_MA', 'itms_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_BOND_INTG_MA', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_BOND_INTG_MA', 'fund_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_BOND_INTG_MA', 'proc_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_BOND_INTG_MA', 'itms_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_CLFD_MIP_MA', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_CLFD_MIP_MA', 'fund_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_CLFD_MIP_MA', 'proc_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_CLFD_REVS_STPR_MA', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_CLFD_REVS_STPR_MA', 'fund_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_CLFD_REVS_STPR_MA', 'proc_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_CLFD_PRDT_MIP_MA', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_CLFD_PRDT_MIP_MA', 'fund_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_CLFD_PRDT_MIP_MA', 'proc_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_EAR_TR', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_EAR_TR', 'fund_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_EAR_TR', 'proc_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_EAR_TR', 'itms_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_EAR_TR', 'ordernum');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_STCK_TR', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_STCK_TR', 'fund_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_STCK_TR', 'proc_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_STCK_TR', 'itms_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_STCK_TR', 'ordernum');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_TAMI_SM', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_TAMI_SM', 'fund_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_TAMI_SM', 'proc_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_CLPR_RECV_SM', 'rcms_finm');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_CLPR_RECV_SM', 'proc_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_CLPR_RECV_SM', 'seq');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_FUND_HT', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_FUND_HT', 'fund_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_FUND_HT', 'proc_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_FUND_INFR_HT', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_FUND_INFR_HT', 'fund_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_FUND_INFR_HT', 'proc_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('TRU_STCK_ITMS_HT', 'proc_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('TRU_STCK_ITMS_HT', 'itms_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_SPA_ITMS_HT', 'proc_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_SPA_ITMS_HT', 'itms_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_FUND_BS', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_FUND_BS', 'fund_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('TRU_MNCM_BS', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('TRU_TRPL_BS', 'trpl_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_MNCM_CLCD_HT', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_MNCM_CLCD_HT', 'mncm_gpcd');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_MNCM_CLCD_HT', 'dtl_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_MNCM_CLCD_HT', 'seq');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_DATE_MNGM_BS', 'prsn_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_BM_STUP_TEMPLT_BS', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_BM_STUP_TEMPLT_BS', 'bm_templt_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_CLFD_BM_TEMPLT_HT', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_CLFD_BM_TEMPLT_HT', 'bm_templt_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_CLFD_BM_TEMPLT_HT', 'strn_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_FUND_OVRV_PDAY_BS', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_FUND_OVRV_PDAY_BS', 'aply_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_FUND_OVRV_PDAY_BS', 'rprt_fund_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('PFO_FUND_OVRV_PDAY_BS', 'dtl_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('RPT_RLGR_TM', 'btch_uniq_id');
INSERT INTO all_tables (table_id, pk_column) VALUES ('TRU_CMN_SRCH_SLCT_TM', 'code_slct_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('TRU_CMN_SRCH_SLCT_TM', 'clmn_id');
INSERT INTO all_tables (table_id, pk_column) VALUES ('TRU_CMN_SRCH_SLCT_TM', 'dtl_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('TRU_SRVC_BTN_LB', 'mncm_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('TRU_SRVC_BTN_LB', 'proc_date');
INSERT INTO all_tables (table_id, pk_column) VALUES ('TRU_SRVC_BTN_LB', 'srvc_code');
INSERT INTO all_tables (table_id, pk_column) VALUES ('TRU_SRVC_BTN_LB', 'seq');

COMMIT;
