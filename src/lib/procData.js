// @ts-nocheck

// ******************************
//#region date related
// ******************************
const nowDTObj = new Date();
export const now = nowDTObj.toISOString().slice(0, 10); // in format '20xx-mm-dd'
const monthDays = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365];

export function dayInYear(mmdd, year) {
	//count the number of day from 1st Jan (1st Jan = 1) in the year
	// assume mmdd is in format 'mm-dd'
	// year needs to be in the range 2001~2099
	if (year <= 2000 || year >= 3000)
		throw new Error(`Year must be in range 2001~2099 (input year ${year})`);
	let m = parseInt(mmdd.slice(0, 2));
	let d = parseInt(mmdd.slice(3));
	// in non-leap year, 02-29 has the same count as 03-01
	return monthDays[m - 1] + d + (year % 4 == 0 && m > 2 ? 1 : 0);
}

/**
 * @param  {ISODate} date - date in string 'yyyy-dd-mm' or 'dd-mm'
 * @param  {ISODate} from - relative to this date 'YYYY-DD-MM'
 * @returns {number} number of day of 'YYYY(+1)-dd-mm' from 'YYYY-DD-MM'
 */
export function dayFrom(date, from = now) {
	let year = parseInt(from.slice(0, 4));
	let dayAtFrom = dayInYear(from.slice(5), year);
	let noyearDate = date.length > 5 ? date.slice(5) : date;
	let diff = dayInYear(noyearDate, year) - dayAtFrom;
	return diff >= 0 ? diff : dayInYear(noyearDate, year + 1) + (365 + (year % 0 != 0) - dayAtFrom);
}

// ******************************
//#region campfire data
// ******************************

const testdata = [
	{
		url: 'https://camp-fire.jp/projects/798003/view',
		title: 'chuLa【飛鳥ことり】生誕祭応援プロジェクト',
		sub: '2024年12月実施予定のchuLa【飛鳥ことり】生誕祭の開催、そして、より盛大にお祝いできるよう支援お願いいたします。ご支援いただいたお金は、イベント支援金と...',
		total: 867000,
		rest: 29,
		per: '終了',
		pricePatrons: [
			{
				price: 3000,
				patrons: 1
			},
			{
				price: 6000,
				patrons: 4
			},
			{
				price: 10000,
				patrons: 18
			},
			{
				price: 50000,
				patrons: 3
			},
			{
				price: 100000,
				patrons: 2
			},
			{
				price: 300000,
				patrons: 1
			}
		],
		subject: {
			group: 'chuLa',
			member: '飛鳥ことり',
			type: '生誕祭'
		},
		start: '2024-10-23',
		end: '2024-11-16'
	},
	{
		url: 'https://camp-fire.jp/projects/797996/view',
		title: 'ZUTTOMOTTO【瀬奈ゆのん】生誕祭応援プロジェクト',
		sub: '2024年12月実施予定のZUTTOMOTTO【瀬奈ゆのん】生誕祭の開催、そして、より盛大にお祝いできるよう支援お願いいたします。ご支援いただいたお金は、イベン...',
		total: 1111205,
		rest: 44,
		per: '終了',
		pricePatrons: [
			{
				price: 3000,
				patrons: 0
			},
			{
				price: 6000,
				patrons: 0
			},
			{
				price: 10000,
				patrons: 33
			},
			{
				price: 50000,
				patrons: 7
			},
			{
				price: 100000,
				patrons: 4
			},
			{
				price: 300000,
				patrons: 0
			}
		],
		subject: {
			group: 'ZUTTOMOTTO',
			member: '瀬奈ゆのん',
			type: '生誕祭'
		},
		start: '2024-10-05',
		end: '2024-11-05'
	}
];

import data from '$lib/data/20260114.json';

/**
 * @param  {Object<string, any>} o
 * @param  {string[]} ks  array of keys
 * @return {Object<string, any>} new object given by taken only keys from ks
 */
const pick = (o, ks) => Object.fromEntries(ks.map((k) => [k, o[k]]));

const LEN = data.length;
console.log(`**** LEN(data) = ${LEN} ****`);

// nested flattening of JSON.  keys become "a.b.c" for original obj { a: {b: {c: ...}}}
// const flattenObj = (o, p = '', r = {}) =>
// 	Object.entries(o).forEach(([k, v]) =>
// 		v && typeof v === 'object' && !Array.isArray(v) ? flattenObj(v, p + k + '.', r) : (r[p + k] = v)
// 	) || r;

export const gpMap = new Map();
export const mbSet = new Set();
export const yrSelection = new Set();

export const processedData = data.reduce((arr, o, i) => {
	if (o.per !== '終了') return arr;
	const r = Object.assign(
		pick(o, ['total', 'url', 'start', 'end', 'pricePatrons', 'eventYear']),
		o.subject
	);
	r.totalpatrons = o.rest;
	// r.averageFund = MoneyString((o.total / o.rest).toFixed(0));
	r.averageFund = o.total / o.rest;
	r.id = i;
	r.period = dayFrom(o.end, o.start);
	// r.eventYear = Number(o.sub.slice(0, 4));
	// if (isNaN(r.eventYear)) {
	// 	console.log('NaN: ', o.sub);
	// }
	r.ppTotal = o.pricePatrons.reduce((res, x) => ((res += x.price * x.patrons), res), 0);
	arr.push(r);

	// process profile data
	yrSelection.add(r.eventYear);
	let mbs = r.member.split(',').map((x) => x.trim());
	for (const m of mbs) {
		mbSet.add(m);
	}
	let idx = Math.max(r.group.indexOf('/'), r.group.indexOf('／'));
	let gps =
		idx > -1 ? [r.group.slice(0, idx).trim(), r.group.slice(idx + 1).trim()] : [r.group.trim()];
	// if (idx > -1) {
	// 	console.log(gps);
	// }
	for (const gp of gps) {
		if (!gpMap.has(gp)) {
			gpMap.set(gp, new Set(mbs));
		} else {
			for (const m of mbs) {
				gpMap.get(gp).add(m);
			}
		}
	}

	return arr;
}, []);
// console.log(processedData);

// export const processedData = [];
export function MoneyString(val, truncAtThousand = false) {
	const str = val.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
	return truncAtThousand ? str.slice(0, -4) : str;
}

// ******************************
//#region profile data
// ******************************
// * using data scraped from elsewhere to populate profile data is not good for this project
// * leave here for possible future use in other projects
// const groupFiles = import.meta.glob('./data/groups/*.json', { eager: true });
// export const heroinesGroups = Object.keys(groupFiles).map((path) => groupFiles[path]);

// const mbMap = new Map();
// for (const gp of heroinesGroups) {
// 	const { id, members } = gp;

// 	for (const mb of members) {
// 		if (!mbMap.has(mb.name)) {
// 			mbMap.set(mb.name, {
// 				name: mb.name,
// 				display: mb.display,
// 				groups: []
// 			});
// 		}
// 		mbMap.get(mb.name).groups.push(id);
// 	}
// }
// export const heroinesMembers = [...mbMap.values()];
