// @ts-nocheck
import registry from './data/agencies.json';
import { createAgencyLoader, validateCatalog, localDataPath } from './agencyCatalog.js';
const snapshots = import.meta.glob(['./data/heroinesCF.json', './data/agencies/*/projects.json']);
const metadata = import.meta.glob('./data/agencies/*/metadata.json', {
	eager: true,
	import: 'default'
});
let catalog = [],
	error = false;
try {
	catalog = validateCatalog(registry, snapshots, metadata);
} catch {
	error = true;
}
export const agencies = catalog;
export const configurationError = error;
export const defaultAgencyId = registry.defaultAgencyId;
export const loadAgency = createAgencyLoader(
	Object.fromEntries(
		agencies.map((agency) => [agency.id, snapshots[localDataPath(agency.databasePath)]])
	)
);
