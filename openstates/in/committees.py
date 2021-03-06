import re

from billy.scrape import NoDataForPeriod
from billy.scrape.committees import CommitteeScraper, Committee

import lxml.html


class INCommitteeScraper(CommitteeScraper):
    state = 'in'

    def scrape(self, chamber, term):
        if term != '2011-2012':
            raise NoDataForPeriod(term)

        chamber_abbr = {'upper': 'S', 'lower': 'H'}[chamber]

        url = ("http://www.in.gov/apps/lsa/session/billwatch/"
               "billinfo?request=getCommitteeList")

        with self.urlopen(url) as page:
            page = lxml.html.fromstring(page)
            page.make_links_absolute(url)

            path = "//a[contains(@href, 'chamber=%s')]" % chamber_abbr
            for link in page.xpath(path):
                name = link.text.strip()
                comm_url = link.attrib['href']
                self.scrape_committee(chamber, term, name, comm_url)

    def scrape_committee(self, chamber, term, name, url):
        with self.urlopen(url) as page:
            page = lxml.html.fromstring(page)

            mlist = page.xpath("//strong[contains(., 'Members:')]")[0].tail
            mlist = re.sub(r'\s+', ' ', mlist)

            committee = Committee(chamber, name)
            committee.add_source(url)

            for member in mlist.split(','):
                member = re.sub(r'R\.M\.(M\.)?$', '', member.strip())
                committee.add_member(member.strip())

            chair = page.xpath("//strong[contains(., 'Chair:')]")[0]
            chair_name = chair.tail.strip()
            if chair_name:
                committee.add_member(chair_name, 'chair')

            vc = page.xpath("//strong[contains(., 'Vice Chair:')]")[0]
            vc_name = vc.tail.strip()
            if vc_name:
                committee.add_member(vc_name, 'vice chair')

            self.save_committee(committee)
