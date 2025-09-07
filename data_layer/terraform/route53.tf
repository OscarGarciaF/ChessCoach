// Look up the existing public hosted zone for the domain you said you already have.
// The domain was purchased on spaceship.com and the nameservers point to Route53.
data "aws_route53_zone" "primary" {
	name         = "interestingchess.com"
	private_zone = false
}

// Apex alias -> CloudFront distribution (created only when var.create_cloudfront = true)
# resource "aws_route53_record" "cdn_apex_alias" {
# 	count   = var.create_cloudfront ? 1 : 0
# 	zone_id = data.aws_route53_zone.primary.zone_id
#     # Use an empty name for the apex record (creates record for the zone apex)
#     name    = ""
# 	type    = "CNAME"

# 	alias {
# 		name                   = aws_cloudfront_distribution.cdn[0].domain_name
# 		zone_id                = aws_cloudfront_distribution.cdn[0].hosted_zone_id
# 		evaluate_target_health = false
# 	}
# }

# // www alias -> CloudFront distribution (created only when var.create_cloudfront = true)
# resource "aws_route53_record" "cdn_www_alias" {
# 	count   = var.create_cloudfront ? 1 : 0
# 	zone_id = data.aws_route53_zone.primary.zone_id
#     # Use 'www' as the record name so Route53 creates www.<zone> in the same hosted zone
#     name    = "www"
# 	type    = "CNAME"

# 	alias {
# 		name                   = aws_cloudfront_distribution.cdn[0].domain_name
# 		zone_id                = aws_cloudfront_distribution.cdn[0].hosted_zone_id
# 		evaluate_target_health = false
# 	}
# }

