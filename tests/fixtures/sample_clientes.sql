-- Listado de clientes de España
-- Plantilla 1000 - Informes y Listados
SELECT 
    c.codigo_cliente,
    c.nombre_fiscal,
    c.cif_nif,
    c.poblacion,
    c.provincia,
    fp.descripcion AS forma_pago,
    c.fecha_alta
FROM clientes c
LEFT JOIN formas_pago fp ON c.codigo_forma_pago = fp.codigo
WHERE c.pais = 'ES'
ORDER BY c.nombre_fiscal
