// @ts-nocheck
import { expect, test } from 'bun:test';
import * as processing from './procData.js';

const record = (group, member, overrides = {}) => ({
	url: 'https://camp-fire.jp/projects/123/view',
	title: 'test',
	per: '終了',
	total: 155500,
	rest: 5,
	start: '2026-01-01',
	end: '2026-01-11',
	eventYear: 2026,
	subject: { group, member, type: '生誕祭' },
	pricePatrons: [{ price: 3000, patrons: 2 }],
	...overrides
});

test('processing separate agencies never shares indexes or mutates raw records', () => {
	expect(typeof processing.processAgencyData).toBe('function');
	const raw = [record('A／B', '甲, 乙'), record('Open', '丙', { per: '募集' })];
	const before = structuredClone(raw);
	const a = processing.processAgencyData(raw);
	const b = processing.processAgencyData([record('C', '丁')]);
	expect([...a.gpMap.keys()]).toEqual(['A', 'B']);
	expect([...b.gpMap.keys()]).toEqual(['C']);
	expect([...a.mbSet]).toEqual(['甲', '乙']);
	expect(a.processedData).toHaveLength(1);
	expect(a.processedData[0]).toMatchObject({
		totalpatrons: 5,
		averageFund: 31100,
		ppTotal: 6000,
		period: 10
	});
	expect(raw).toEqual(before);
	a.processedData[0].pricePatrons[0].patrons = 99;
	expect(raw).toEqual(before);
});

test('empty data and zero supporters produce safe values', () => {
	expect(typeof processing.processAgencyData).toBe('function');
	expect(processing.processAgencyData([]).processedData).toEqual([]);
	expect(
		processing.processAgencyData([record('A', '甲', { rest: 0 })]).processedData[0].averageFund
	).toBeNull();
});

test('funding periods use actual calendar years including leap days', () => {
	expect(processing.dayFrom('2023-01-19', '2022-12-21')).toBe(29);
	expect(processing.dayFrom('2024-03-01', '2024-02-28')).toBe(2);
	expect(processing.dayFrom('2026-01-31', '2025-11-01')).toBe(91);
});
