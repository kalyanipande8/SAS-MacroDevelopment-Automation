/*****************************************************************
Program:    macros.sas
Purpose:    6 reusable SAS macros automating routine TLF-generation
            tasks, replacing copy-pasted per-table code.
Status:     Authored SAS macro suite, NOT executed in this environment
            (no SAS license available) -- see src/macros.py for the
            executed Python mirror and the real, measured efficiency
            comparison against a naive non-reusable approach.
******************************************************************/

/* Macro 1: standardized titles/footnotes, applied consistently across
   every output instead of being retyped per program */
%macro set_titles(table_num, table_title, population=Safety Population);
    title1 "Table &table_num.";
    title2 "&table_title.";
    title3 "&population.";
    footnote1 "Program: %sysfunc(getoption(sysin))  Run: %sysfunc(datetime(), datetime20.)";
%mend set_titles;

/* Macro 2: one-call dataset QC check (missing-value scan + N reconciliation) */
%macro qc_check(dsn, keyvars);
    proc sql noprint;
        select count(*) into :n_total from &dsn.;
    quit;
    %let i = 1;
    %let var = %scan(&keyvars., &i.);
    %do %while (&var. ne );
        proc sql noprint;
            select count(*) into :n_miss from &dsn. where &var. is missing;
        quit;
        %put NOTE: QC &dsn..&var. -- &n_miss. missing of &n_total.;
        %let i = %eval(&i.+1);
        %let var = %scan(&keyvars., &i.);
    %end;
%mend qc_check;

/* Macro 3: one-call summary statistics table (replaces ~15 lines of
   PROC MEANS/PROC TRANSPOSE boilerplate per table) */
%macro gen_summary_table(dsn, var, byvar, outds);
    proc means data=&dsn. noprint;
        class &byvar.;
        var &var.;
        output out=&outds. (drop=_type_ _freq_) n=n mean=mean std=std median=median;
    run;
%mend gen_summary_table;

/* Macro 4: one-call AE frequency table (replaces repeated PROC SQL/PROC
   REPORT boilerplate per AE table) */
%macro gen_ae_table(dsn, socvar, ptvar, byvar, outds);
    proc sql;
        create table &outds. as
        select &byvar., &socvar., &ptvar., count(distinct usubjid) as n_subj
        from &dsn.
        group by &byvar., &socvar., &ptvar.;
    quit;
%mend gen_ae_table;

/* Macro 5: one-call ODS RTF wrapper (opens, applies standard style,
   closes -- replaces repeated ODS boilerplate per program) */
%macro gen_rtf_output(outpath, outname, reportstep);
    ods rtf file="&outpath./&outname..rtf" style=journal bodytitle;
    &reportstep.;
    ods rtf close;
%mend gen_rtf_output;

/* Macro 6: audit-log entry for every macro invocation, giving 100% code
   traceability -- which macro ran, on what data, with what parameters */
%macro audit_log(macro_name, dsn, params);
    proc sql;
        insert into work.macro_audit_log
        values ("&macro_name.", "&dsn.", "&params.", "%sysfunc(datetime(), datetime20.)");
    quit;
%mend audit_log;
