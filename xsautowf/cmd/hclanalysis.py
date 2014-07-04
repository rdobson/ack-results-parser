"""Python script to analyze HCL related telemetry"""

from xsautowf.cmd.processsubmission import JIRA, ArgumentParser
import datetime


def time_track(inputdate):
    """Prints Weekly Tickets Created and Resolved from the input day
       till Today"""
    type_hcl = """type='HCL Submission' """
    l_res_date = """and resolutiondate>='%d/%d/%d'"""
    u_res_date = """and resolutiondate<='%d/%d/%d'"""
    query_reslvd_tkts = type_hcl + l_res_date + u_res_date
    l_crtd_date = """and createdDate>='%d/%d/%d'"""
    u_crtd_date = """ and createdDate<='%d/%d/%d'"""
    query_crtd_tkts = type_hcl + l_crtd_date + u_crtd_date
    inputdate = datetime.datetime(int(inputdate.split('-')[0]),
                                  int(inputdate.split('-')[1]),
                                  int(inputdate.split('-')[2]))
    today = datetime.datetime.today()

    date = inputdate
    nextweek_firstday = datetime.datetime.today()
    while (nextweek_firstday - today).days <= 0:
        week_firstday = date - datetime.timedelta(date.weekday())
        week_endday = week_firstday + datetime.timedelta(7)

        nextweek_firstday = week_endday + datetime.timedelta(1)
        reslvd_tkts = JIRA.search_issues(query_reslvd_tkts %
                                         (week_firstday.year,
                                          week_firstday.month,
                                          week_firstday.day,
                                          week_endday.year,
                                          week_endday.month,
                                          week_endday.day))
        print "Resolved Tickets between %s to %s = %d" % (week_firstday,
                                                          week_endday,
                                                          len(reslvd_tkts))
        crtd_tkts = JIRA.search_issues(query_crtd_tkts % (week_firstday.year,
                                                          week_firstday.month,
                                                          week_firstday.day,
                                                          week_endday.year,
                                                          week_endday.month,
                                                          week_endday.day))
        print "Created Tickets between %s to %s = %d\n" % (week_firstday,
                                                           week_endday,
                                                           len(crtd_tkts))
        date = nextweek_firstday


def main():
    """Entry Point"""
    data_parser = ArgumentParser()
    data_parser.add_argument("-d", "--date", dest="date", required=True,
                             help="Enter Date format: YYYY-MM-DD")
    cmdargs = data_parser.parse_args()
    time_track(cmdargs.date)
