-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Nov 19, 2025 at 03:11 AM
-- Server version: 9.1.0
-- PHP Version: 8.3.14

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `kasir_koperasi`
--

-- --------------------------------------------------------

--
-- Table structure for table `barang`
--

DROP TABLE IF EXISTS `barang`;
CREATE TABLE IF NOT EXISTS `barang` (
  `id_barang` int NOT NULL AUTO_INCREMENT,
  `kode_barang` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `barcode` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `keterangan` text COLLATE utf8mb4_general_ci,
  `nama_barang` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `id_kategori` int DEFAULT NULL,
  `id_supplier` int DEFAULT NULL,
  `dibuat_pada` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_barang`),
  UNIQUE KEY `kode_barang` (`kode_barang`),
  UNIQUE KEY `barcode` (`barcode`),
  KEY `idx_barcode` (`barcode`),
  KEY `fk_barang_kategori` (`id_kategori`),
  KEY `id_supplier` (`id_supplier`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `barang`
--

INSERT INTO `barang` (`id_barang`, `kode_barang`, `barcode`, `keterangan`, `nama_barang`, `id_kategori`, `id_supplier`, `dibuat_pada`) VALUES
(1, 'BRG001', '089686420678', NULL, 'INDOFOOD KECAP MANIS 580 M REF', 1, 1, '2025-11-16 15:15:54'),
(2, 'BRG002', '9556001131959', NULL, 'NESTLE CERELAC BERAS PUTIH 120 GR', 1, 2, '2025-11-16 18:45:01'),
(3, 'BRG003', '9556001978400', NULL, 'NESTLE KACANG HIJAU 120G', NULL, 2, '2025-11-17 01:19:25');

-- --------------------------------------------------------

--
-- Table structure for table `customer`
--

DROP TABLE IF EXISTS `customer`;
CREATE TABLE IF NOT EXISTS `customer` (
  `id_customer` int NOT NULL AUTO_INCREMENT,
  `kode_customer` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `nama_customer` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `telepon` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `alamat` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `tipe` enum('reguler','member','vip') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'reguler',
  `catatan` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `status` enum('aktif','nonaktif') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'aktif',
  `dibuat_pada` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `diperbarui_pada` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_customer`),
  UNIQUE KEY `kode_customer` (`kode_customer`),
  KEY `idx_kode` (`kode_customer`),
  KEY `idx_status` (`status`),
  KEY `idx_tipe` (`tipe`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `customer`
--

INSERT INTO `customer` (`id_customer`, `kode_customer`, `nama_customer`, `telepon`, `email`, `alamat`, `tipe`, `catatan`, `status`, `dibuat_pada`, `diperbarui_pada`) VALUES
(1, 'CUST001', 'Brian Farrel Evandhika', '08112618282', 'brianfe25@gmail.com', 'Puri Indah Blok G No 38 RT4/RW11 Karangklesem Purwokerto Selatan Banyumas', 'member', NULL, 'aktif', '2025-11-16 08:21:18', '2025-11-16 08:21:18');

-- --------------------------------------------------------

--
-- Table structure for table `detail_barang`
--

DROP TABLE IF EXISTS `detail_barang`;
CREATE TABLE IF NOT EXISTS `detail_barang` (
  `id_detail` int NOT NULL AUTO_INCREMENT,
  `id_barang` int NOT NULL,
  `harga_beli` decimal(12,2) NOT NULL,
  `margin` decimal(6,2) DEFAULT '0.00',
  `harga_jual` decimal(12,2) NOT NULL,
  `stok` int DEFAULT '0',
  `dibuat_pada` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_detail`),
  KEY `id_barang` (`id_barang`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `detail_barang`
--

INSERT INTO `detail_barang` (`id_detail`, `id_barang`, `harga_beli`, `margin`, `harga_jual`, `stok`, `dibuat_pada`) VALUES
(1, 1, 15000.00, 33.33, 30000.00, 0, '2025-11-16 15:15:54'),
(2, 2, 20000.00, 50.00, 30000.00, 0, '2025-11-16 18:45:01'),
(3, 1, 16500.00, 21.21, 30000.00, 0, '2025-11-16 20:41:32'),
(4, 1, 19500.00, 2.56, 30000.00, 0, '2025-11-16 21:14:40'),
(5, 1, 20000.00, 50.00, 30000.00, 0, '2025-11-16 21:46:47'),
(6, 3, 10000.00, 0.00, 10000.00, 80, '2025-11-17 01:19:25'),
(7, 1, 25000.00, 0.00, 30000.00, 5, '2025-11-18 00:51:18'),
(8, 2, 25000.00, 0.00, 30000.00, 80, '2025-11-18 00:54:26');

-- --------------------------------------------------------

--
-- Table structure for table `detail_pembelian`
--

DROP TABLE IF EXISTS `detail_pembelian`;
CREATE TABLE IF NOT EXISTS `detail_pembelian` (
  `id_detail_pembelian` int NOT NULL AUTO_INCREMENT,
  `id_pembelian` int NOT NULL,
  `id_detail` int NOT NULL,
  `jumlah` int NOT NULL,
  `harga_beli` decimal(12,2) NOT NULL,
  `dibuat_pada` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_detail_pembelian`),
  KEY `id_pembelian` (`id_pembelian`),
  KEY `id_detail` (`id_detail`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `detail_pembelian`
--

INSERT INTO `detail_pembelian` (`id_detail_pembelian`, `id_pembelian`, `id_detail`, `jumlah`, `harga_beli`, `dibuat_pada`) VALUES
(1, 1, 7, 10, 25000.00, '2025-11-18 00:51:18'),
(2, 2, 8, 100, 25000.00, '2025-11-18 00:54:25');

-- --------------------------------------------------------

--
-- Table structure for table `detail_penjualan`
--

DROP TABLE IF EXISTS `detail_penjualan`;
CREATE TABLE IF NOT EXISTS `detail_penjualan` (
  `id_detail_penjualan` int NOT NULL AUTO_INCREMENT,
  `id_penjualan` int NOT NULL,
  `id_detail` int NOT NULL,
  `jumlah` int NOT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  `diskon` int DEFAULT '0',
  `total` int DEFAULT '0',
  `dibuat_pada` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_detail_penjualan`),
  KEY `id_penjualan` (`id_penjualan`),
  KEY `id_detail` (`id_detail`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `detail_penjualan`
--

INSERT INTO `detail_penjualan` (`id_detail_penjualan`, `id_penjualan`, `id_detail`, `jumlah`, `subtotal`, `diskon`, `total`, `dibuat_pada`) VALUES
(1, 1, 5, 10, 300000.00, 15000, 285000, '2025-11-18 00:44:20'),
(2, 1, 2, 10, 300000.00, 15000, 285000, '2025-11-18 00:44:20'),
(3, 1, 6, 10, 100000.00, 5000, 95000, '2025-11-18 00:44:20'),
(4, 2, 7, 5, 150000.00, 0, 150000, '2025-11-18 00:51:49'),
(5, 3, 8, 20, 600000.00, 60000, 540000, '2025-11-18 00:55:09'),
(6, 4, 6, 10, 100000.00, 20000, 80000, '2025-11-18 01:27:03');

-- --------------------------------------------------------

--
-- Table structure for table `kategori`
--

DROP TABLE IF EXISTS `kategori`;
CREATE TABLE IF NOT EXISTS `kategori` (
  `id_kategori` int NOT NULL AUTO_INCREMENT,
  `kode_kategori` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `nama_kategori` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `icon_kategori` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `deskripsi` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `dibuat_pada` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `diperbarui_pada` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_kategori`),
  UNIQUE KEY `kode_kategori` (`kode_kategori`),
  KEY `idx_kode` (`kode_kategori`),
  KEY `idx_nama` (`nama_kategori`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `kategori`
--

INSERT INTO `kategori` (`id_kategori`, `kode_kategori`, `nama_kategori`, `icon_kategori`, `deskripsi`, `dibuat_pada`, `diperbarui_pada`) VALUES
(1, 'KAT001', 'Bumbu Dapur', NULL, NULL, '2025-11-16 08:19:44', '2025-11-16 08:19:44');

-- --------------------------------------------------------

--
-- Table structure for table `pembelian`
--

DROP TABLE IF EXISTS `pembelian`;
CREATE TABLE IF NOT EXISTS `pembelian` (
  `id_pembelian` int NOT NULL AUTO_INCREMENT,
  `id_user` int DEFAULT NULL,
  `id_petugas` int DEFAULT NULL,
  `id_supplier` int DEFAULT NULL,
  `tanggal` datetime DEFAULT CURRENT_TIMESTAMP,
  `tempat_pembelian` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`id_pembelian`),
  KEY `id_user` (`id_user`),
  KEY `fk_pembelian_petugas` (`id_petugas`),
  KEY `fk_pembelian_supplier` (`id_supplier`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `pembelian`
--

INSERT INTO `pembelian` (`id_pembelian`, `id_user`, `id_petugas`, `id_supplier`, `tanggal`, `tempat_pembelian`) VALUES
(1, NULL, 1, NULL, '2025-11-18 00:51:18', NULL),
(2, NULL, 1, NULL, '2025-11-18 00:54:26', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `penjualan`
--

DROP TABLE IF EXISTS `penjualan`;
CREATE TABLE IF NOT EXISTS `penjualan` (
  `id_penjualan` int NOT NULL AUTO_INCREMENT,
  `id_user` int DEFAULT NULL,
  `id_petugas` int DEFAULT NULL,
  `id_customer` int DEFAULT NULL,
  `nama_pembeli` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `nomor_telepon` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `metode_pembayaran` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'Tunai',
  `keterangan` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `tanggal` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `total_item` int DEFAULT '0',
  `total_harga` decimal(12,2) DEFAULT '0.00',
  PRIMARY KEY (`id_penjualan`),
  KEY `fk_penjualan_petugas` (`id_petugas`),
  KEY `fk_penjualan_customer` (`id_customer`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `penjualan`
--

INSERT INTO `penjualan` (`id_penjualan`, `id_user`, `id_petugas`, `id_customer`, `nama_pembeli`, `nomor_telepon`, `metode_pembayaran`, `keterangan`, `tanggal`, `total_item`, `total_harga`) VALUES
(1, NULL, 1, NULL, NULL, NULL, 'Tunai', NULL, '2025-11-18 00:44:20', 0, 665000.00),
(2, NULL, 1, NULL, NULL, NULL, 'Tunai', NULL, '2025-11-18 00:51:50', 0, 150000.00),
(3, NULL, 1, NULL, NULL, NULL, 'Tunai', NULL, '2025-11-18 00:55:09', 0, 540000.00),
(4, NULL, 1, NULL, NULL, NULL, 'Tunai', NULL, '2025-11-18 01:27:03', 0, 80000.00);

-- --------------------------------------------------------

--
-- Table structure for table `petugas`
--

DROP TABLE IF EXISTS `petugas`;
CREATE TABLE IF NOT EXISTS `petugas` (
  `id_petugas` int NOT NULL AUTO_INCREMENT,
  `nama_petugas` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `telepon` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `alamat` text COLLATE utf8mb4_general_ci,
  `jabatan` enum('admin','kasir','supervisor','gudang') COLLATE utf8mb4_general_ci DEFAULT 'kasir',
  `status` enum('aktif','nonaktif') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'aktif',
  `dibuat_pada` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `diperbarui_pada` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_petugas`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `petugas`
--

INSERT INTO `petugas` (`id_petugas`, `nama_petugas`, `username`, `password`, `telepon`, `email`, `alamat`, `jabatan`, `status`, `dibuat_pada`, `diperbarui_pada`) VALUES
(1, 'John Doe', 'admin', 'admin1234', '081234567890', 'petugas@example.com', '123 Maple Street, Springfield', 'admin', 'aktif', '2025-11-16 07:55:52', '2025-11-16 08:57:07'),
(2, 'User', 'User', '123456', '0812345678910', 'user@example.com', 'user', 'kasir', 'aktif', '2025-11-16 13:32:06', '2025-11-19 02:13:53'),
(3, 'aryo', 'aryo', '123456', '0811111111', 'aryo@example.com', NULL, 'gudang', 'aktif', '2025-11-19 02:24:26', '2025-11-19 03:09:55'),
(4, 'udin', 'udin', '123456', '0899999999', 'udin@example.com', 'oke', '', 'aktif', '2025-11-19 02:51:29', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `supplier`
--

DROP TABLE IF EXISTS `supplier`;
CREATE TABLE IF NOT EXISTS `supplier` (
  `id_supplier` int NOT NULL AUTO_INCREMENT,
  `kode_supplier` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `nama_supplier` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `nama_kontak` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `telepon` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `alamat` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `keterangan` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `status` enum('aktif','nonaktif') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'aktif',
  `dibuat_pada` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `diperbarui_pada` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_supplier`),
  UNIQUE KEY `kode_supplier` (`kode_supplier`),
  KEY `idx_kode` (`kode_supplier`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `supplier`
--

INSERT INTO `supplier` (`id_supplier`, `kode_supplier`, `nama_supplier`, `nama_kontak`, `telepon`, `email`, `alamat`, `keterangan`, `status`, `dibuat_pada`, `diperbarui_pada`) VALUES
(1, 'SUP001', 'PT Indofood Sukses Makmur', 'John Doe', '081234567890', 'john.doe@example.com', '123 Maple Street, Springfield', NULL, 'aktif', '2025-11-16 08:13:21', '2025-11-16 08:57:28'),
(2, 'SUP002', 'PT Nestle', 'Jane Smith', '081398765432', 'jane.smith@example.com', '45 Oakwood Avenue, Greenville', NULL, 'aktif', '2025-11-16 11:44:06', '2025-11-16 11:44:06');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE IF NOT EXISTS `users` (
  `id_user` int NOT NULL AUTO_INCREMENT,
  `nama_user` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `role` enum('admin','kasir') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'kasir',
  `dibuat_pada` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_user`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Stand-in structure for view `view_laporan`
-- (See below for the actual view)
--
DROP VIEW IF EXISTS `view_laporan`;
CREATE TABLE IF NOT EXISTS `view_laporan` (
`harga_beli` decimal(12,2)
,`harga_jual` decimal(12,2)
,`id_transaksi` int
,`jenis_transaksi` varchar(9)
,`jumlah` int
,`kasir` varchar(100)
,`subtotal` decimal(22,2)
,`tanggal` datetime
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `view_stok_barang`
-- (See below for the actual view)
--
DROP VIEW IF EXISTS `view_stok_barang`;
CREATE TABLE IF NOT EXISTS `view_stok_barang` (
`dibuat_pada` datetime
,`harga_beli` decimal(12,2)
,`harga_jual` decimal(12,2)
,`kode_barang` varchar(50)
,`margin` decimal(6,2)
,`nama_barang` varchar(100)
,`stok` int
);

-- --------------------------------------------------------

--
-- Structure for view `view_laporan`
--
DROP TABLE IF EXISTS `view_laporan`;

DROP VIEW IF EXISTS `view_laporan`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `view_laporan`  AS SELECT 'Penjualan' AS `jenis_transaksi`, `p`.`id_penjualan` AS `id_transaksi`, `u`.`nama_user` AS `kasir`, `p`.`tanggal` AS `tanggal`, `dp`.`jumlah` AS `jumlah`, `d`.`harga_beli` AS `harga_beli`, `d`.`harga_jual` AS `harga_jual`, (`dp`.`jumlah` * `d`.`harga_jual`) AS `subtotal` FROM (((`penjualan` `p` join `users` `u` on((`p`.`id_user` = `u`.`id_user`))) join `detail_penjualan` `dp` on((`p`.`id_penjualan` = `dp`.`id_penjualan`))) join `detail_barang` `d` on((`dp`.`id_detail` = `d`.`id_detail`)))union all select 'Pembelian' AS `jenis_transaksi`,`pb`.`id_pembelian` AS `id_transaksi`,`u`.`nama_user` AS `kasir`,`pb`.`tanggal` AS `tanggal`,`dpb`.`jumlah` AS `jumlah`,`dpb`.`harga_beli` AS `harga_beli`,NULL AS `harga_jual`,(`dpb`.`jumlah` * `dpb`.`harga_beli`) AS `subtotal` from ((`pembelian` `pb` join `users` `u` on((`pb`.`id_user` = `u`.`id_user`))) join `detail_pembelian` `dpb` on((`pb`.`id_pembelian` = `dpb`.`id_pembelian`)))  ;

-- --------------------------------------------------------

--
-- Structure for view `view_stok_barang`
--
DROP TABLE IF EXISTS `view_stok_barang`;

DROP VIEW IF EXISTS `view_stok_barang`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `view_stok_barang`  AS SELECT `b`.`kode_barang` AS `kode_barang`, `b`.`nama_barang` AS `nama_barang`, `d`.`harga_beli` AS `harga_beli`, `d`.`margin` AS `margin`, `d`.`harga_jual` AS `harga_jual`, `d`.`stok` AS `stok`, `d`.`dibuat_pada` AS `dibuat_pada` FROM (`barang` `b` join `detail_barang` `d` on((`b`.`id_barang` = `d`.`id_barang`))) ORDER BY `b`.`nama_barang` ASC ;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `barang`
--
ALTER TABLE `barang`
  ADD CONSTRAINT `barang_ibfk_1` FOREIGN KEY (`id_supplier`) REFERENCES `supplier` (`id_supplier`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_barang_kategori` FOREIGN KEY (`id_kategori`) REFERENCES `kategori` (`id_kategori`) ON DELETE SET NULL;

--
-- Constraints for table `detail_barang`
--
ALTER TABLE `detail_barang`
  ADD CONSTRAINT `detail_barang_ibfk_1` FOREIGN KEY (`id_barang`) REFERENCES `barang` (`id_barang`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `detail_pembelian`
--
ALTER TABLE `detail_pembelian`
  ADD CONSTRAINT `detail_pembelian_ibfk_1` FOREIGN KEY (`id_pembelian`) REFERENCES `pembelian` (`id_pembelian`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `detail_pembelian_ibfk_2` FOREIGN KEY (`id_detail`) REFERENCES `detail_barang` (`id_detail`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `detail_penjualan`
--
ALTER TABLE `detail_penjualan`
  ADD CONSTRAINT `fk_detail_barang` FOREIGN KEY (`id_detail`) REFERENCES `detail_barang` (`id_detail`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_penjualan` FOREIGN KEY (`id_penjualan`) REFERENCES `penjualan` (`id_penjualan`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `pembelian`
--
ALTER TABLE `pembelian`
  ADD CONSTRAINT `fk_pembelian_petugas` FOREIGN KEY (`id_petugas`) REFERENCES `petugas` (`id_petugas`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_pembelian_supplier` FOREIGN KEY (`id_supplier`) REFERENCES `supplier` (`id_supplier`) ON DELETE SET NULL,
  ADD CONSTRAINT `pembelian_ibfk_1` FOREIGN KEY (`id_user`) REFERENCES `users` (`id_user`) ON DELETE SET NULL ON UPDATE CASCADE;

--
-- Constraints for table `penjualan`
--
ALTER TABLE `penjualan`
  ADD CONSTRAINT `fk_penjualan_customer` FOREIGN KEY (`id_customer`) REFERENCES `customer` (`id_customer`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_penjualan_petugas` FOREIGN KEY (`id_petugas`) REFERENCES `petugas` (`id_petugas`) ON DELETE SET NULL ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
