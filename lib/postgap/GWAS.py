#! /usr/bin/env python

"""

Copyright [1999-2018] EMBL-European Bioinformatics Institute

Licensed under the Apache License, Version 2.0 (the "License")
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

		 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

"""

	Please email comments or questions to the public Ensembl
	developers list at <http://lists.ensembl.org/mailman/listinfo/dev>.

	Questions may also be sent to the Ensembl help desk at
	<http://www.ensembl.org/Help/Contact>.

"""
import re
import requests
import json
import sys
import logging
from pprint import pformat

import postgap.REST
import postgap.Globals
from postgap.DataModel import *
from postgap.Utils import *
from postgap.GWAS_Lead_Snp_Orientation import *

class GWAS_source(object):
	def run(self, diseases, iris):
		"""

			Returns all GWAS SNPs associated to a disease in this source
			Args:
			* [ string ] (trait descriptions)
			* [ string ] (trait Ontology IRIs)
			Returntype: [ GWAS_Association ]

		"""
		assert False, "This stub should be defined"

class GWASCatalog(GWAS_source):
	display_name = 'GWAS Catalog'

	def run(self, diseases, iris):
		"""
			Returns all GWAS SNPs associated to a disease in GWAS Catalog
			Args:
			* [ string ] (trait descriptions)
			* [ string ] (trait Ontology IRIs)
			Returntype: [ GWAS_Association ]
		"""

		if iris is not None and len(iris) > 0:
			res = concatenate(self.query(query) for query in iris)
		else:
			res = concatenate(self.query(query) for query in diseases)

		logging.debug("\tFound %i GWAS SNPs associated to diseases (%s) or EFO IDs (%s) in GWAS Catalog" % (len(res), ", ".join(diseases), ", ".join(iris)))

		return res

	def query(self, efo):
		logging.info("Querying GWAS catalog for " + efo);
		server = 'http://www.ebi.ac.uk'
		url = '/gwas/rest/api/efoTraits/search/findByEfoUri?uri=%s' % (efo)

		hash = postgap.REST.get(server, url)

		'''
			hash looks like this:
			
			{
				"_embedded": {
					"efoTraits": [
						{
							"trait": "diabetes mellitus",
							"uri": "http://www.ebi.ac.uk/efo/EFO_0000400",
							"_links": {
								"self": {
									"href": "http://wwwdev.ebi.ac.uk/gwas/beta/rest/api/efoTraits/71"
								},
								"efoTrait": {
									"href": "http://wwwdev.ebi.ac.uk/gwas/beta/rest/api/efoTraits/71"
								},
								"studies": {
									"href": "http://wwwdev.ebi.ac.uk/gwas/beta/rest/api/efoTraits/71/studies"
								},
								"associations": {
									"href": "http://wwwdev.ebi.ac.uk/gwas/beta/rest/api/efoTraits/71/associations"
								}
							}
						}
					]
				},
				"_links": {
					"self": {
						"href": "http://wwwdev.ebi.ac.uk/gwas/beta/rest/api/efoTraits/search/findByUri?uri=http://www.ebi.ac.uk/efo/EFO_0000400"
					}
				},
				"page": {
					"size": 20,
					"totalElements": 1,
					"totalPages": 1,
					"number": 0
				}
			}
		'''

		list_of_GWAS_Associations = []

		efoTraits = hash["_embedded"]["efoTraits"]
		
		for efoTraitHash in efoTraits:
			efoTraitLinks = efoTraitHash["_links"]
			efoTraitName  = efoTraitHash["trait"]

			logging.info("Querying Gwas rest server for SNPs associated with " + efoTraitName)

			association_rest_response = efoTraitLinks["associations"]
			association_url = association_rest_response["href"]
			try:
				# e.g.: http://wwwdev.ebi.ac.uk/gwas/beta/rest/api/efoTraits/71/associations
				#
				association_response = postgap.REST.get(association_url, "")
			except:
				continue
			
			associations = association_response["_embedded"]["associations"]
			
			'''
				associations has this structure:
				
				[

					{
						"riskFrequency": "NR",
						"pvalueDescription": null,
						"pvalueMantissa": 2,
						"pvalueExponent": -8,
						"multiSnpHaplotype": false,
						"snpInteraction": false,
						"snpType": "known",
						"standardError": 0.0048,
						"range": "[NR]",
						"description": null,
						"orPerCopyNum": null,
						"betaNum": 0.0266,
						"betaUnit": "unit",
						"betaDirection": "increase",
						"lastMappingDate": "2016-12-24T07:36:49.000+0000",
						"lastUpdateDate": "2016-11-25T14:37:53.000+0000",
						"pvalue": 2.0E-8,
						"_links": {
							"self": {
								"href": "http://wwwdev.ebi.ac.uk/gwas/beta/rest/api/associations/16513018"
							},
							"association": {
								"href": "http://wwwdev.ebi.ac.uk/gwas/beta/rest/api/associations/16513018"
							},
							"study": {
								"href": "http://wwwdev.ebi.ac.uk/gwas/beta/rest/api/associations/16513018/study"
							},
							"snps": {
								"href": "http://wwwdev.ebi.ac.uk/gwas/beta/rest/api/associations/16513018/snps"
							},
							"loci": {
								"href": "http://wwwdev.ebi.ac.uk/gwas/beta/rest/api/associations/16513018/loci"
							},
							"efoTraits": {
								"href": "http://wwwdev.ebi.ac.uk/gwas/beta/rest/api/associations/16513018/efoTraits"
							},
							"genes": {
								"href": "http://wwwdev.ebi.ac.uk/gwas/beta/rest/api/associations/16513018/genes"
							}
						}
					},
				...
				]
			'''
			logging.info("Received " + str(len(associations)) + " associations with SNPs.")
			logging.info("Fetching SNPs and pvalues.")

			for current_association in associations:
				# e.g. snp_url can be: http://wwwdev.ebi.ac.uk/gwas/beta/rest/api/associations/16513018/snps
				#
				snp_url = current_association["_links"]["snps"]["href"]
				snp_response = postgap.REST.get(snp_url, "")
				"""
				Example response:
				{
					_embedded: {
						singleNucleotidePolymorphisms: [
								{
									rsId: "rs3757057",
									merged: 0,
									functionalClass: "intron_variant",
									lastUpdateDate: "2016-12-25T03:48:35.194+0000",
									_links: {}
									}
								]
					},
					_links: {}
				}
				"""
				singleNucleotidePolymorphisms = snp_response["_embedded"]["singleNucleotidePolymorphisms"]

				if (len(singleNucleotidePolymorphisms) == 0):
					# sys.exit("Got no snp for a pvalue!")
					continue

				study_url = current_association["_links"]["study"]["href"]
				study_response = postgap.REST.get(study_url, "")
				"""
				Example response:
				{
					author: "Barber MJ",
					publicationDate: "2010-03-22T00:00:00.000+0000",
					publication: "PLoS One",
					title: "Genome-wide association of lipid-lowering response to statins in combined study populations.",
					initialSampleSize: "3,928 European ancestry individuals",
					replicateSampleSize: "NA",
					pubmedId: "20339536",
					gxe: false,
					gxg: false,
					genomewideArray: true,
					targetedArray: false,
					snpCount: 2500000,
					qualifier: "~",
					imputed: true,
					pooled: false,
					studyDesignComment: null,
					accessionId: "GCST000635",
					fullPvalueSet: false,
					_links: {}
				}
				"""
				study_id = study_response['accessionId']
				pubmedId = study_response["publicationInfo"]["pubmedId"]

				diseaseTrait = study_response["diseaseTrait"]["trait"]
				ancestries = study_response["ancestries"]
				"""
				Example response:
				{
					_embedded: {
						ancestries: [
								{
									type: "initial",
									numberOfIndividuals: 3928,
									description: "Los Angeles, CA; ",
									previouslyReported: null,
									notes: null,
									_links: {}
									}
								]
						},
						_links: {}
				}
				"""
				sample_size = sum(int(ancestry['numberOfIndividuals']) for ancestry in ancestries if ancestry['numberOfIndividuals'] is not None)

				for current_snp in singleNucleotidePolymorphisms:
					is_dbSNP_accession = "rs" in current_snp["rsId"]
					
					if not(is_dbSNP_accession):
						logging.warning("Did not get a valid dbSNP accession: (" + current_snp["rsId"] + ") from " + snp_url)
						continue
					
					if current_snp["rsId"] == '6':
						continue
					if current_snp["rsId"][-1] == u'\xa0':
						current_snp["rsId"] = current_snp["rsId"].strip()

					logging.debug("    received association with snp rsId: " + '{:12}'.format(current_snp["rsId"]) + " with a pvalue of " + str(current_association["pvalue"]))
					
					associations_href = current_snp["_links"]["associations"]["href"]
					associations = postgap.REST.get(associations_href, ext="")

					riskAlleles = []
					loci = current_association["loci"]
					for locus in loci:
						strongestRiskAlleles = locus["strongestRiskAlleles"]
						riskAlleles.append(strongestRiskAlleles)

					for riskAllele in riskAlleles:
						try:
						
							if gwas_risk_alleles_present_in_reference(riskAllele):
								risk_alleles_present_in_reference = True
								logging.info("Risk allele is present in reference");
							else:
								risk_alleles_present_in_reference = False
								logging.info("Risk allele is not present in reference");
						
						except none_of_the_risk_alleles_is_a_substitution_exception as e:
							logging.warning(str(e))
							logging.warning("Skipping this snp.")
							continue
						
						except variant_mapping_is_ambiguous_exception:
							logging.warning("The variant mapping is ambiguous.")
							logging.warning("Skipping this snp.")
							continue
						
						except some_alleles_present_in_reference_others_not_exception as e:
							logging.warning(str(e));
							logging.warning("Skipping this snp.")
							continue
						
						except no_dbsnp_accession_for_snp_exception as e:
							logging.warning(str(e))
							logging.warning("Skipping this snp.")
							continue

						except base_in_allele_missing_exception as e:
							logging.warning(str(e));
							logging.warning("Skipping this snp.")
							continue

						except cant_determine_base_at_snp_in_reference_exception as e:
							logging.warning(str(e));
							logging.warning("Skipping this snp.")
							continue
						
						except gwas_data_integrity_exception as e:
							logging.warning(str(e));
							logging.warning("Skipping this snp.")
							continue

						ci_start_value = None
						ci_end_value = None

						if not current_association["range"] == None:
							ci_values = re.findall('\d+\.\d+', current_association["range"])

							if ci_values:
								try:
									ci_start_value = ci_values[0]
									ci_end_value = ci_values[1]
								except:
									pass


						list_of_GWAS_Associations.append(
							GWAS_Association(
								disease = Disease(
									name = efoTraitName,
									efo  = efo
								),
								reported_trait = diseaseTrait,
								snp     = current_snp["rsId"],
								pvalue  = current_association["pvalue"],
								pvalue_description = current_association["pvalueDescription"],
								source  = 'GWAS Catalog',
								publication = 'PMID' + pubmedId,
								study   = study_id,
								sample_size = sample_size,
								
								# For fetching additional information like risk allele later, if needed.
								# E.g.: http://wwwdev.ebi.ac.uk/gwas/beta/rest/api/singleNucleotidePolymorphisms/9765
								rest_hash = current_snp,
								risk_alleles_present_in_reference = risk_alleles_present_in_reference,
								
								odds_ratio                 = current_association["orPerCopyNum"],
								odds_ratio_ci_start        = ci_start_value,
								odds_ratio_ci_end 		   = ci_end_value,
								beta_coefficient           = current_association["betaNum"],
								beta_coefficient_unit      = current_association["betaUnit"],
								beta_coefficient_direction = current_association["betaDirection"]
							)
						)

		if len(list_of_GWAS_Associations) > 0:
			logging.info("Fetched " +  str(len(list_of_GWAS_Associations)) + " SNPs and pvalues.")
		if len(list_of_GWAS_Associations) == 0:
			logging.info("Found no associated SNPs and pvalues.")
	
		return list_of_GWAS_Associations

class Neale_UKB(GWAS_source):
	display_name = "Neale_UKB"
	def run(self, diseases, iris):
		"""

			Returns all GWAS SNPs associated to a disease in Neale_UKB
			Args:
			* [ string ] (trait descriptions)
			* [ string ] (trait Ontology IRIs)
			Returntype: [ GWAS_Association ]

		"""
		logger = logging.getLogger(__name__)
		
		# This database does not have EFOs so give up early if unneeded
		if diseases == None or len(diseases) == 0:
			return []

		file = open(postgap.Globals.DATABASES_DIR+"/Neale_UKB.txt")
		res = [ self.get_association(line, diseases, iris) for line in file ]
		res = filter(lambda X: X is not None, res)

		logger.info("\tFound %i GWAS SNPs associated to diseases (%s) or EFO IDs (%s) in Neale_UKB" % (len(res), ", ".join(diseases), ", ".join(iris)))

		return res

	def get_association(self, line, diseases, iris):
		'''
			Neale_UKB file format:
		'''
		try:
			snp, disease, reported_trait, p_value, sample_size, source, study, odds_ratio, beta_coefficient, beta_coefficient_direction = line.strip().split('\t')
		except:
			return None




		if reported_trait in diseases:
			return GWAS_Association(
				pvalue = float(p_value),
				pvalue_description = None,
				snp = snp,
				disease = None,
				reported_trait = reported_trait + " " + disease,
				source = 'UK Biobank',
				publication = source,
				study = None,
				sample_size = sample_size,
				odds_ratio = None,
				beta_coefficient = beta_coefficient,
				beta_coefficient_unit = None,
				beta_coefficient_direction = beta_coefficient_direction
			)
		else:
			return None


class GRASP(GWAS_source):
	display_name = "GRASP"
	def run(self, diseases, iris):
		"""

			Returns all GWAS SNPs associated to a disease in GRASP
			Args:
			* [ string ] (trait descriptions)
			* [ string ] (trait Ontology IRIs)
			Returntype: [ GWAS_Association ]

		"""
		file = open(postgap.Globals.DATABASES_DIR+"/GRASP.txt")
		res = [ self.get_association(line, diseases, iris) for line in file ]
		res = filter(lambda X: X is not None, res)

		logging.info("\tFound %i GWAS SNPs associated to diseases (%s) or EFO IDs (%s) in GRASP" % (len(res), ", ".join(diseases), ", ".join(iris)))

		return res

	def get_association(self, line, diseases, iris):
		'''

			GRASP file format:
			1. NHLBIkey
			2. HUPfield
			3. LastCurationDate
			4. CreationDate
			5. SNPid(dbSNP134)
			6. chr(hg19)
			7. pos(hg19)
			8. PMID
			9. SNPid(in paper)
			10. LocationWithinPaper
			11. Pvalue
			12. Phenotype
			13. PaperPhenotypeDescription
			14. PaperPhenotypeCategories
			15. DatePub
			16. InNHGRIcat(as of 3/31/12)
			17. Journal
			18. Title
			19. IncludesMale/Female Only Analyses
			20. Exclusively Male/Female
			21. Initial Sample Description
			22. Replication Sample Description
			23. Platform [SNPs passing QC]
			24. GWASancestryDescription
			25. TotalSamples(discovery+replication)
			26. TotalDiscoverySamples
			27. European Discovery
			28. African Discovery
			29. East Asian Discovery
			30. Indian/South Asian Discovery
			31. Hispanic Discovery
			32. Native Discovery
			33. Micronesian Discovery
			34. Arab/ME Discovery
			35. Mixed Discovery
			36. Unspecified Discovery
			37. Filipino Discovery
			38. Indonesian Discovery
			39. Total replication samples
			40. European Replication
			41. African Replication
			42. East Asian Replication
			43. Indian/South Asian Replication
			44. Hispanic Replication
			45. Native Replication
			46. Micronesian Replication
			47. Arab/ME Replication
			48. Mixed Replication
			49. Unspecified Replication
			50. Filipino Replication
			51. Indonesian Replication
			52. InGene
			53. NearestGene
			54. InLincRNA
			55. InMiRNA
			56. InMiRNABS
			57. dbSNPfxn
			58. dbSNPMAF
			59. dbSNPalleles/het/se
			60. dbSNPvalidation
			XX61. dbSNPClinStatus
			XX62. ORegAnno
			XX63. ConservPredTFBS
			XX64. HumanEnhancer
			XX65. RNAedit
			XX66. PolyPhen2
			XX67. SIFT
			XX68. LS-SNP
			XX69. UniProt
			XX70. EqtlMethMetabStudy
			71. EFO string

		'''
		items = line.rstrip().split('\t')
		for iri in items[70].split(','):
			if iri in iris:
				try:
					return GWAS_Association(
						pvalue = float(items[10]),
						pvalue_description = None,
						snp = "rs" + items[4],
						disease = Disease(name = postgap.EFO.term(iri), efo = iri),
						reported_trait = items[12].decode('latin1'),
						source = self.display_name,
						publication = items[7],
						study = None,
						sample_size = int(items[24]),
						odds_ratio = None,
						odds_ratio_ci_start = None,
						odds_ratio_ci_end = None,
						beta_coefficient = None,
						beta_coefficient_unit = None,
						beta_coefficient_direction = None,
						rest_hash = None,
						risk_alleles_present_in_reference = None
					)
				except:
					return None

		if items[12] in diseases:
			iri = items[70].split(',')[0]
			try:
				return GWAS_Association(
					pvalue = float(items[10]),
					pvalue_description = None,
					snp = "rs" + items[4],
					disease = Disease(name = postgap.EFO.term(iri), efo = iri),
					reported_trait = items[12].decode('latin1'),
					source = self.display_name,
					publication = items[7],
					study = None,
					sample_size = int(items[24]),
					odds_ratio = None,
					odds_ratio_ci_start=None,
					odds_ratio_ci_end=None,
					beta_coefficient = None,
					beta_coefficient_unit = None,
					beta_coefficient_direction = None,
					rest_hash = None,
					risk_alleles_present_in_reference = None
				)
			except:
				return None

		if items[12] in diseases:
			iri = items[70].split(',')[0]
			return GWAS_Association(
				pvalue = float(items[10]),
				snp = "rs" + items[4],
				disease = Disease(name = postgap.EFO.term(iri), efo = iri),
				reported_trait = items[12].decode('latin1'),
				source = self.display_name,
				study = items[7],
				sample_size = int(items[24]),
				odds_ratio = None,
				odds_ratio_ci_start=None,
				odds_ratio_ci_end=None,
				beta_coefficient = None,
				beta_coefficient_unit = None,
				beta_coefficient_direction = None,
				rest_hash = None,
				risk_alleles_present_in_reference = None
			)

		return None

class Phewas_Catalog(GWAS_source):
	display_name = "Phewas Catalog"
	
	def run(self, diseases, iris):
		"""

			Returns all GWAS SNPs associated to a disease in PhewasCatalog
			Args:
			* [ string ] (trait descriptions)
			* [ string ] (trait Ontology IRIs)
			Returntype: [ GWAS_Association ]

		"""
		file = open(postgap.Globals.DATABASES_DIR+"/Phewas_Catalog.txt")
		res = [ self.get_association(line, diseases, iris) for line in file ]
		res = filter(lambda X: X is not None, res)

		logging.info("\tFound %i GWAS SNPs associated to diseases (%s) or EFO IDs (%s) in Phewas Catalog" % (len(res), ", ".join(diseases), ", ".join(iris)))

		return res

	def get_association(self, line, diseases, iris):
		'''

			Phewas Catalog format:
			1. chromosome
			2. snp
			3. phewas phenotype
			4. cases
			5. p-value
			6. odds-ratio
			7. gene_name
			8. phewas code
			9. gwas-associations
			10. [Inserte] EFO identifier (or N/A)

		'''
		items = line.rstrip().split('\t')
		for iri in items[9].split(','):
			if iri in iris:
				return GWAS_Association (
					pvalue = float(items[4]),
					pvalue_description = None,
					snp = items[1],
					disease = Disease(name = postgap.EFO.term(iri), efo = iri), 
					reported_trait = items[2],
					source = self.display_name,
					publication = "PMID24270849",
					study = None,
					sample_size = int(items[3]),
					odds_ratio = float(items[5]),
					odds_ratio_ci_start=None,
					odds_ratio_ci_end=None,
					beta_coefficient = None,
					beta_coefficient_unit = None,
					beta_coefficient_direction = None,
					rest_hash = None,
					risk_alleles_present_in_reference = None
				)

		if items[2] in diseases: 
			iri = items[9].split(',')[0]
			return GWAS_Association (
				pvalue = float(items[4]),
				pvalue_description = None,
				snp = items[1],
				disease = Disease(name = postgap.EFO.term(iri), efo = iri), 
				reported_trait = items[2],
				source = self.display_name,
				publication = "PMID24270849",
				study = None,
				sample_size = int(items[3]),
				odds_ratio = float(items[5]),
				odds_ratio_ci_start=None,
				odds_ratio_ci_end=None,
				beta_coefficient = None,
				beta_coefficient_unit = None,
				beta_coefficient_direction = None,
				rest_hash = None,
				risk_alleles_present_in_reference = None
			)

		return None

class GWAS_File(GWAS_source):
	display_name = "GWAS File"
	
	def create_gwas_association_collector(self):
		
		class gwas_association_collector:
			
			def __init__(self):
				self.found_list = []
			
			def add_to_found_list(self, gwas_association):
				self.found_list.append(gwas_association)
			
			def get_found_list(self):
				return self.found_list
		
		return gwas_association_collector()

	
	def run(self, diseases, iris):
		"""

			Returns all GWAS SNPs associated to a disease in known gwas files
			Args:
			* [ string ] (trait descriptions)
			* [ string ] (trait Ontology IRIs)
			Returntype: [ GWAS_Association ]

		"""
		
		gwas_data_file = postgap.Globals.GWAS_SUMMARY_STATS_FILE
			
		if gwas_data_file is None:
			return None
		
		logging.info( "gwas_data_file = " + gwas_data_file )
		
		pvalue_filtered_gwas_associations = self.create_gwas_association_collector()
		
		pvalue_filter = self.create_pvalue_filter(pvalue_threshold = postgap.Globals.GWAS_PVALUE_CUTOFF)
		
		self.parse_gwas_data_file(
			gwas_data_file                    = gwas_data_file,
			want_this_gwas_association_filter = pvalue_filter,
			callback                          = pvalue_filtered_gwas_associations.add_to_found_list,
			max_lines_to_return_threshold     = None,
		)
		
		logging.info( "Found " + str(len(pvalue_filtered_gwas_associations.get_found_list())) + " gwas associations with a pvalue of " + str(postgap.Globals.GWAS_PVALUE_CUTOFF) + " or less.")
		
		return pvalue_filtered_gwas_associations.get_found_list()
	
	def create_gwas_cluster_with_pvalues_from_file(self, gwas_cluster, gwas_data_file):

		ld_gwas_associations = self.create_gwas_association_collector()
		
		self.parse_gwas_data_file(
			gwas_data_file                = gwas_data_file, 
			wanted_snps                   = [ld_snp.rsID for ld_snp in gwas_cluster.ld_snps],
			callback                      = ld_gwas_associations.add_to_found_list,
			max_lines_to_return_threshold = len(gwas_cluster.ld_snps)
		)
		logging.info( "ld_gwas_associations.found_list: " + pformat(ld_gwas_associations.get_found_list()) )
		
		ld_snps_converted_to_gwas_snps = []
		
		for ld_snp in gwas_cluster.ld_snps:
			
			gwas_associations_for_ld_snp = filter(lambda x : ld_snp.rsID == x.snp, ld_gwas_associations.get_found_list())
			
			# If one could be found, add that.
			if len(gwas_associations_for_ld_snp) == 1:
				
				logging.info("Found " + ld_snp.rsID + " in the file! All good.")
				gwas_association = gwas_associations_for_ld_snp[0] 
				assert type(gwas_association) is GWAS_Association, "gwas_association is GWAS_Association."
			
				gwas_snp = GWAS_SNP(
					snp      = gwas_association.snp,
					pvalue   = gwas_association.pvalue,
					z_score  = None,
					evidence = [ gwas_association ],
					beta     = gwas_association.beta_coefficient
				)
				ld_snps_converted_to_gwas_snps.append(gwas_snp)
			
			# If more than one assocation was found: error.	
			if len(gwas_associations_for_ld_snp) > 1:
				logging.info("Found more than one matching assocation for " + ld_snp.rsID + " in the file. Bad!")
				sys.exit(1)
			
			# If the snp wasn't found, add it as a regular snp.
			if len(gwas_associations_for_ld_snp) == 0:
				logging.info("Found no matching assocation for " + ld_snp.rsID + " in the file. Including it as regular snp.")
				
		proper_gwas_cluster = GWAS_Cluster(
			gwas_snps = gwas_cluster.gwas_snps,
			ld_snps = ld_snps_converted_to_gwas_snps,
			ld_matrix = None,
			z_scores = None,
			gwas_configuration_posteriors = None
		)
		return proper_gwas_cluster
	
	def create_pvalue_filter(self, pvalue_threshold):
		return lambda pvalue: float(pvalue) < pvalue_threshold
	
	def parse_gwas_data_file(
			self, 
			gwas_data_file, 
			callback,
			wanted_snps = None, 
			want_this_gwas_association_filter = None,
			max_lines_to_return_threshold = None,
		):
		

		file = open(gwas_data_file)
		column_labels = file.readline().strip().split('\t')

		number_of_lines_returned = 0
		for line in file:
			items = line.rstrip().split('\t')
			
			parsed = dict()
			for column_index, column_label in enumerate(column_labels):
				parsed[column_label] = items[column_index]
			
			if want_this_gwas_association_filter is not None and not want_this_gwas_association_filter(parsed["p-value"]):
				continue
			
			if wanted_snps is not None and not parsed['variant_id'] in wanted_snps:
				continue

			try:
				# TODO insert study info (from command line? config file?)
				gwas_association = GWAS_Association(
					pvalue                            = float(parsed["p-value"]),
					pvalue_description		  = 'Manual',
					snp                               = parsed["variant_id"],
					disease                           = Disease(name = 'Manual', efo = 'EFO_Manual'),
					reported_trait                    = "Manual",
					source                            = "Manual",
					publication			  = "PMID000",
					study                             = "Manual",
					sample_size                       = 1000,
					odds_ratio                        = None,
					odds_ratio_ci_start		  = None,
					odds_ratio_ci_end		  = None,
					beta_coefficient                  = float(parsed["beta"]),
					beta_coefficient_unit             = "Manual",
					beta_coefficient_direction        = "Manual",
					rest_hash                         = None,
					risk_alleles_present_in_reference = None,
				)
			except ValueError:
				continue

			callback(gwas_association)
			
			number_of_lines_returned += 1
			if max_lines_to_return_threshold is not None and number_of_lines_returned>=max_lines_to_return_threshold:
				break

class GWAS_DB(GWAS_source):
	display_name = "GWAS DB"
	
	def run(self, diseases, iris):
		"""

			Returns all GWAS SNPs associated to a disease in GWAS_DB
			Args:
			* [ string ] (trait descriptions)
			* [ string ] (trait Ontology IRIs)
			Returntype: [ GWAS_Association ]

		"""
		file = open(postgap.Globals.DATABASES_DIR+"/GWAS_DB.txt")
	
		res = [ self.get_association(line, diseases, iris) for line in file ]
		res = filter(lambda X: X is not None, res)

		logging.info("\tFound %i GWAS SNPs associated to diseases (%s) or EFO IDs (%s) in GWAS DB" % (len(res), ", ".join(diseases), ", ".join(iris)))

		return res

	def get_association(self, line, diseases, iris):
		'''

			GWAS DB data
			1. CHR
			2. POS
			3. SNPID
			4. P_VALUE
			5. PUBMED ID
			6. MESH_TERM
			7. EFO_ID

		'''
		items = line.rstrip().split('\t')
		for iri in items[6].split(','):
			if iri in iris:
				return GWAS_Association(
					pvalue = float(items[3]),
					pvalue_description = None,
					snp = items[2],
					disease = Disease(name = postgap.EFO.term(iri), efo = iri),
					reported_trait = items[5].decode('latin1'),
					source = self.display_name,
					publication = items[4],
					study = None,
					sample_size = "N/A",
					odds_ratio = None,
					odds_ratio_ci_start=None,
					odds_ratio_ci_end=None,
					beta_coefficient = None,
					beta_coefficient_unit = None,
					beta_coefficient_direction = None,
					rest_hash = None,
					risk_alleles_present_in_reference = None
				)

		if items[5] in diseases:
			iri = items[6].split(',')[0]
			return GWAS_Association(
				pvalue = float(items[3]),
				pvalue_description = None,
				snp = items[2],
				disease = Disease(name = postgap.EFO.term(iri), efo = iri),
				reported_trait = items[5].decode('latin1'),
				source = self.display_name,
				publication = items[4],
				study = None,
				sample_size = "N/A",
				odds_ratio = None,
				odds_ratio_ci_start=None,
				odds_ratio_ci_end=None,
				beta_coefficient = None,
				beta_coefficient_unit = None,
				beta_coefficient_direction = None,
				rest_hash = None,
				risk_alleles_present_in_reference = None
			)

		return None


def get_filtered_subclasses(subclasses_filter):

	subclasses_filter = [sc.replace('_', ' ') for sc in subclasses_filter]
	return [subclass for subclass in sources if subclass.display_name in subclasses_filter]


sources = GWAS_source.__subclasses__()
