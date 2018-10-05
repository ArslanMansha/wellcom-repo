"""Scrap products from wellcome.com."""
import json
import scrapy


class WelcomeSpider(scrapy.Spider):
    """Spider."""
    name = "welcome"
    start_urls = ["https://www.wellcome.com.hk/wd2shop/docroot/en/das.xml"]
    cookie_url = "https://www.wellcome.com.hk/wd2/jsp/sys/Sf_render.jsp?hf_locale_id=en&" \
                 "hf_s_id=WD11&hf_srv_id=Av_jcart&hs_set_ddc_by_dist_id=7&" \
                 "hs_set_new_order_cnc_ctr_id=SHOP251"
    cookie_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    product_url = "https://www.wellcome.com.hk/wd2/jsp/sys/Sf_render.jsp?hs_dept_id={}&" \
                  "hs_srch_page_no=1&hs_rec_per_page={}&hs_action_id=submit&" \
                  "hf_srv_id=Pv_jpdt_brw&hf_s_id=WD11"

    def parse(self, response):
        """Gets and dictionarize the hierarchy."""
        departments = dict(zip(response.xpath("//Department/@id").extract(),
                               response.xpath("//Department/Name/text()").extract()))
        aisle = dict(zip(response.xpath("//Aisle/@id").extract(),
                         response.xpath("//Aisle/Name/text()").extract()))
        shelf = dict(zip(response.xpath("//Shelf/@id").extract(),
                         response.xpath("//Shelf/Name/text()").extract()))
        yield response.follow(self.cookie_url, callback=self.set_cookie, headers=self.cookie_headers,
                              meta={"departments": departments, "aisles": aisle, "shelves": shelf})

    def set_cookie(self, response):
        """Sets cookie."""
        department_ids = response.meta['departments'].keys()
        for department_id in department_ids:
            product_url = self.product_url.format(department_id, 12)
            yield response.follow(product_url, callback=self.parse_product_pagination,
                                  meta=response.meta)

    def parse_product_pagination(self, response):
        """Gets total number of products in section."""
        products = json.loads(response.body_as_unicode())
        yield response.follow(response.url.replace("12", str(products['bi_rec_cnt'])),
                              callback=self.parse_product, meta=response.meta)

    @staticmethod
    def parse_product(response):
        """Parses products."""
        products = json.loads(response.body_as_unicode())['bvc_pdt']
        for product in products:
            product.update({"Department": response.meta['departments'][str(product['bj_dept_id'])],
                            "Aisle": response.meta['aisles'][str(product['bj_aisle_id'])],
                            "Shelf": response.meta['shelves'][str(product['bj_shelf_id'])]})
            yield product
