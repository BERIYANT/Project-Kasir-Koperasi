-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Oct 22, 2025 at 02:58 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

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

CREATE TABLE `barang` (
  `id_barang` int(11) NOT NULL,
  `kode_barang` varchar(50) NOT NULL,
  `nama_barang` varchar(100) NOT NULL,
  `dibuat_pada` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `barang`
--

INSERT INTO `barang` (`id_barang`, `kode_barang`, `nama_barang`, `dibuat_pada`) VALUES
(1, 'BRG001', 'Indomie Goreng', '2025-10-22 18:08:17'),
(2, 'BRG002', 'Sabun Lifebuoy', '2025-10-22 18:08:17'),
(3, 'BRG003', 'Kopi Kapal Api', '2025-10-22 18:08:17');

-- --------------------------------------------------------

--
-- Table structure for table `detail_barang`
--

CREATE TABLE `detail_barang` (
  `id_detail` int(11) NOT NULL,
  `id_barang` int(11) NOT NULL,
  `harga_beli` decimal(12,2) NOT NULL,
  `margin` decimal(6,2) DEFAULT 0.00,
  `harga_jual` decimal(12,2) NOT NULL,
  `stok` int(11) DEFAULT 0,
  `dibuat_pada` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `detail_barang`
--

INSERT INTO `detail_barang` (`id_detail`, `id_barang`, `harga_beli`, `margin`, `harga_jual`, `stok`, `dibuat_pada`) VALUES
(1, 1, 5000.00, 20.00, 15000.00, 40, '2025-10-22 18:08:17'),
(2, 2, 3000.00, 30.00, 3900.00, 40, '2025-10-22 18:08:17'),
(3, 3, 2000.00, 25.00, 2500.00, 60, '2025-10-22 18:08:17'),
(9, 1, 10000.00, 50.00, 15000.00, 20, '2025-10-22 19:31:16');

-- --------------------------------------------------------

--
-- Table structure for table `detail_pembelian`
--

CREATE TABLE `detail_pembelian` (
  `id_detail_pembelian` int(11) NOT NULL,
  `id_pembelian` int(11) NOT NULL,
  `id_detail` int(11) NOT NULL,
  `jumlah` int(11) NOT NULL,
  `harga_beli` decimal(12,2) NOT NULL,
  `dibuat_pada` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `detail_pembelian`
--

INSERT INTO `detail_pembelian` (`id_detail_pembelian`, `id_pembelian`, `id_detail`, `jumlah`, `harga_beli`, `dibuat_pada`) VALUES
(3, 2, 2, 1, 3000.00, '2025-10-22 18:34:59'),
(8, 7, 9, 20, 10000.00, '2025-10-22 19:31:16');

-- --------------------------------------------------------

--
-- Table structure for table `detail_penjualan`
--

CREATE TABLE `detail_penjualan` (
  `id_detail_penjualan` int(11) NOT NULL,
  `id_penjualan` int(11) NOT NULL,
  `id_detail` int(11) NOT NULL,
  `jumlah` int(11) NOT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  `dibuat_pada` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `detail_penjualan`
--

INSERT INTO `detail_penjualan` (`id_detail_penjualan`, `id_penjualan`, `id_detail`, `jumlah`, `subtotal`, `dibuat_pada`) VALUES
(2, 4, 1, 5, 55000.00, '2025-10-22 19:30:37'),
(3, 5, 1, 5, 75000.00, '2025-10-22 19:31:35');

-- --------------------------------------------------------

--
-- Table structure for table `pembelian`
--

CREATE TABLE `pembelian` (
  `id_pembelian` int(11) NOT NULL,
  `id_user` int(11) DEFAULT NULL,
  `tanggal` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `pembelian`
--

INSERT INTO `pembelian` (`id_pembelian`, `id_user`, `tanggal`) VALUES
(1, NULL, '2025-10-22 18:08:56'),
(2, NULL, '2025-10-22 18:34:59'),
(3, NULL, '2025-10-22 18:35:40'),
(4, NULL, '2025-10-22 18:40:08'),
(5, NULL, '2025-10-22 18:45:41'),
(6, NULL, '2025-10-22 18:53:34'),
(7, NULL, '2025-10-22 19:31:16');

-- --------------------------------------------------------

--
-- Table structure for table `penjualan`
--

CREATE TABLE `penjualan` (
  `id_penjualan` int(11) NOT NULL,
  `id_user` int(11) DEFAULT NULL,
  `tanggal` datetime NOT NULL DEFAULT current_timestamp(),
  `total_item` int(11) DEFAULT 0,
  `total_harga` decimal(12,2) DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `penjualan`
--

INSERT INTO `penjualan` (`id_penjualan`, `id_user`, `tanggal`, `total_item`, `total_harga`) VALUES
(3, NULL, '2025-10-22 19:29:35', 0, 55000.00),
(4, NULL, '2025-10-22 19:30:37', 0, 55000.00),
(5, NULL, '2025-10-22 19:31:35', 0, 75000.00);

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id_user` int(11) NOT NULL,
  `nama_user` varchar(100) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin','kasir') DEFAULT 'kasir',
  `dibuat_pada` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id_user`, `nama_user`, `username`, `password`, `role`, `dibuat_pada`) VALUES
(1, 'Admin Koperasi', 'admin', 'admin123', 'admin', '2025-10-22 18:08:17'),
(2, 'Kasir Utama', 'kasir1', 'kasir123', 'kasir', '2025-10-22 18:08:17');

-- --------------------------------------------------------

--
-- Stand-in structure for view `view_laporan`
-- (See below for the actual view)
--
CREATE TABLE `view_laporan` (
`jenis_transaksi` varchar(9)
,`id_transaksi` int(11)
,`kasir` varchar(100)
,`tanggal` datetime
,`jumlah` int(11)
,`harga_beli` decimal(12,2)
,`harga_jual` decimal(12,2)
,`subtotal` decimal(22,2)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `view_stok_barang`
-- (See below for the actual view)
--
CREATE TABLE `view_stok_barang` (
`kode_barang` varchar(50)
,`nama_barang` varchar(100)
,`harga_beli` decimal(12,2)
,`margin` decimal(6,2)
,`harga_jual` decimal(12,2)
,`stok` int(11)
,`dibuat_pada` datetime
);

-- --------------------------------------------------------

--
-- Structure for view `view_laporan`
--
DROP TABLE IF EXISTS `view_laporan`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `view_laporan`  AS SELECT 'Penjualan' AS `jenis_transaksi`, `p`.`id_penjualan` AS `id_transaksi`, `u`.`nama_user` AS `kasir`, `p`.`tanggal` AS `tanggal`, `dp`.`jumlah` AS `jumlah`, `d`.`harga_beli` AS `harga_beli`, `d`.`harga_jual` AS `harga_jual`, `dp`.`jumlah`* `d`.`harga_jual` AS `subtotal` FROM (((`penjualan` `p` join `users` `u` on(`p`.`id_user` = `u`.`id_user`)) join `detail_penjualan` `dp` on(`p`.`id_penjualan` = `dp`.`id_penjualan`)) join `detail_barang` `d` on(`dp`.`id_detail` = `d`.`id_detail`))union all select 'Pembelian' AS `jenis_transaksi`,`pb`.`id_pembelian` AS `id_transaksi`,`u`.`nama_user` AS `kasir`,`pb`.`tanggal` AS `tanggal`,`dpb`.`jumlah` AS `jumlah`,`dpb`.`harga_beli` AS `harga_beli`,NULL AS `harga_jual`,`dpb`.`jumlah` * `dpb`.`harga_beli` AS `subtotal` from ((`pembelian` `pb` join `users` `u` on(`pb`.`id_user` = `u`.`id_user`)) join `detail_pembelian` `dpb` on(`pb`.`id_pembelian` = `dpb`.`id_pembelian`))  ;

-- --------------------------------------------------------

--
-- Structure for view `view_stok_barang`
--
DROP TABLE IF EXISTS `view_stok_barang`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `view_stok_barang`  AS SELECT `b`.`kode_barang` AS `kode_barang`, `b`.`nama_barang` AS `nama_barang`, `d`.`harga_beli` AS `harga_beli`, `d`.`margin` AS `margin`, `d`.`harga_jual` AS `harga_jual`, `d`.`stok` AS `stok`, `d`.`dibuat_pada` AS `dibuat_pada` FROM (`barang` `b` join `detail_barang` `d` on(`b`.`id_barang` = `d`.`id_barang`)) ORDER BY `b`.`nama_barang` ASC ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `barang`
--
ALTER TABLE `barang`
  ADD PRIMARY KEY (`id_barang`),
  ADD UNIQUE KEY `kode_barang` (`kode_barang`);

--
-- Indexes for table `detail_barang`
--
ALTER TABLE `detail_barang`
  ADD PRIMARY KEY (`id_detail`),
  ADD KEY `id_barang` (`id_barang`);

--
-- Indexes for table `detail_pembelian`
--
ALTER TABLE `detail_pembelian`
  ADD PRIMARY KEY (`id_detail_pembelian`),
  ADD KEY `id_pembelian` (`id_pembelian`),
  ADD KEY `id_detail` (`id_detail`);

--
-- Indexes for table `detail_penjualan`
--
ALTER TABLE `detail_penjualan`
  ADD PRIMARY KEY (`id_detail_penjualan`),
  ADD KEY `id_penjualan` (`id_penjualan`),
  ADD KEY `id_detail` (`id_detail`);

--
-- Indexes for table `pembelian`
--
ALTER TABLE `pembelian`
  ADD PRIMARY KEY (`id_pembelian`),
  ADD KEY `id_user` (`id_user`);

--
-- Indexes for table `penjualan`
--
ALTER TABLE `penjualan`
  ADD PRIMARY KEY (`id_penjualan`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id_user`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `barang`
--
ALTER TABLE `barang`
  MODIFY `id_barang` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `detail_barang`
--
ALTER TABLE `detail_barang`
  MODIFY `id_detail` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `detail_pembelian`
--
ALTER TABLE `detail_pembelian`
  MODIFY `id_detail_pembelian` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `detail_penjualan`
--
ALTER TABLE `detail_penjualan`
  MODIFY `id_detail_penjualan` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `pembelian`
--
ALTER TABLE `pembelian`
  MODIFY `id_pembelian` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `penjualan`
--
ALTER TABLE `penjualan`
  MODIFY `id_penjualan` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id_user` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Constraints for dumped tables
--

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
  ADD CONSTRAINT `pembelian_ibfk_1` FOREIGN KEY (`id_user`) REFERENCES `users` (`id_user`) ON DELETE SET NULL ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
